"""Views relating to user actions."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from requests import HTTPError
from sentry_sdk import capture_exception

from portal.forms import ExternalUserProfileForm, RPIUserProfileForm
from portal.models import User
from portal.services import discord, github


@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """Renders the logged in user's profile and saves changes when edited."""
    if request.method == "POST":
        form = ExternalUserProfileForm(request.POST, instance=request.user) if request.user.role == User.EXTERNAL else RPIUserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            messages.success(request, "Your profile was updated.")
            form.save()
            return redirect(reverse("profile"))
    else:
        form = ExternalUserProfileForm(instance=request.user) if request.user.role == User.EXTERNAL else RPIUserProfileForm(instance=request.user)

    return TemplateResponse(
        request,
        "portal/auth/profile.html",
        {"form": form},
    )


def impersonate(request: HttpRequest) -> HttpResponse:
    """
    Force a login as the desired user. Only possible in DEBUG mode locally
    and with a logged in superuser in production.
    """
    if settings.DEBUG or request.user.is_superuser:
        email = request.POST["email"]
        user = User.objects.get(email=email)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return redirect("/")


def start_discord_flow(request: HttpRequest) -> HttpResponse:
    return redirect(discord.DISCORD_OAUTH2_URL)


@login_required
def unlink_discord(request: HttpRequest) -> HttpResponse:
    """Disconnects the logged in user's Discord account."""
    response = discord.kick_user_from_server(request.user.discord_user_id)
    response.raise_for_status()
    request.user.discord_user_id = None

    try:
        request.user.save()
        messages.info(request, "Successfully unlinked your Discord account.")
    except Exception as e:
        capture_exception(e)
        messages.error(request, "Failed to unlink your Discord account...")

    return redirect(reverse("profile"))


def discord_flow_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET.get("code")
    if not code:
        raise BadRequest("Denied Discord consent.")

    # Complete Discord OAuth2 flow to get tokens and then Discord user id
    try:
        discord_user_tokens = discord.get_tokens(code)
        discord_access_token = discord_user_tokens["access_token"]
        discord_user_info = discord.get_user_info(discord_access_token)
    except HTTPError as e:
        capture_exception(e)
        messages.error(request, "Yikes! Failed to link your Discord.")
        return redirect(reverse("profile"))

    discord_user_id = discord_user_info["id"]

    if request.user.is_authenticated:
        request.user.discord_user_id = discord_user_id
        try:
            request.user.save()
            messages.success(
                request,
                f"Successfully linked Discord account @{discord.discord_username(discord_user_info)} to your profile.",
            )
        except IntegrityError:
            messages.warning(
                request,
                f"Discord account @{discord.discord_username(discord_user_info)} is already linked "
                "to another user!",
            )
            return redirect(reverse("profile"))

        # Attempt to add the Discord user to the server
        try:
            joined_server = discord.upsert_server_member(
                discord_access_token,
                discord_user_info["id"],
                request.user.display_name,
                [settings.DISCORD_VERIFIED_ROLE_ID]
                if request.user.is_approved
                else None,
            )

            if joined_server:
                # If the user was added to the server
                messages.success(request, "Added you to the RCOS Discord server!")

        except HTTPError as e:
            capture_exception(e)
            messages.warning(request, "Failed to add you to the RCOS Discord server...")

    else:
        # Login
        try:
            user = User.objects.get(discord_user_id=discord_user_id)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        except User.DoesNotExist:
            messages.warning(
                request,
                "No RCOS account found that matches your Discord. "
                "Please sign in with email first "
                "and then link your Discord account on your profile!",
            )
            return redirect(reverse("magiclink:login") + "?next=/auth/discord")

    return redirect(reverse("profile"))


def start_github_flow(request: HttpRequest) -> HttpResponse:
    return redirect(github.GITHUB_AUTH_URL)


def github_flow_callback(request: HttpRequest) -> HttpResponse:
    code = request.GET.get("code")
    if not code:
        raise BadRequest

    # Complete OAuth2 flow to receive access token and then GitHub username
    try:
        github_user_tokens = github.get_tokens(code)
        github_access_token = github_user_tokens["access_token"]
        client = github.client_factory(github_access_token)
        github_username = github.get_user_username(client)
    except HTTPError as e:
        capture_exception(e)
        messages.error(request, "Yikes! Failed to link your GitHub.")
        return redirect(reverse("profile"))
    except KeyError:
        messages.error(request, "Failed to link your GitHub. Try again.")
        return redirect(reverse("profile"))

    # Determine whether to link user or log them in based on an existing link
    if request.user.is_authenticated:
        request.user.github_username = github_username
        try:
            request.user.save()
            messages.success(
                request,
                f"Successfully linked GitHub account @{github_username} "
                "to your profile.",
            )
        except IntegrityError:
            messages.warning(
                request,
                f"GitHub account @{github_username} is already linked to another user!",
            )
    else:
        # Login user with that linked GitHub account
        try:
            user = User.objects.get(github_username=github_username)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        except User.DoesNotExist:
            messages.warning(
                request,
                "No RCOS account found that matches your GitHub. "
                "Please sign in with email first and then "
                "link your GitHub account on your profile!",
            )
            return redirect(reverse("magiclink:login") + "?next=/auth/github")

    return redirect(reverse("profile"))


@login_required
def unlink_github(request: HttpRequest) -> HttpResponse:
    """Disconnects the logged in user's GitHub account."""
    request.user.github_username = None

    try:
        request.user.save()
        messages.info(request, "Successfully unlinked your GitHub account.")
    except Exception as e:
        capture_exception(e)
        messages.error(request, "Failed to unlink your GitHub account...")

    return redirect(reverse("profile"))
