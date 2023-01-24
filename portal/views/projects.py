from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.edit import CreateView

from portal.forms import ProposeProjectForm
from portal.services import github

from ..models import Enrollment, Project, ProjectPitch, Semester
from . import (
    SearchableListView,
    SemesterFilteredDetailView,
    SemesterFilteredListView,
    UserRequiresSetupMixin,
)


class ProjectIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/projects/index.html"
    context_object_name = "projects"

    # Default to all approved projects
    queryset = (
        Project.objects.filter(is_approved=True)
        .prefetch_related("tags", "pitches")
        .select_related("owner", "organization")
    )
    semester_filter_key = "enrollments__semester"
    search_fields = (
        "name",
        "owner__first_name",
        "owner__last_name",
        "owner__rcs_id",
        "description",
        "tags__name",
    )

    def get_queryset(self):
        """Apply filters (semester is already handled)"""
        queryset = super().get_queryset()

        self.is_seeking_members = self.request.GET.get("is_seeking_members") == "yes"
        if self.is_seeking_members:
            queryset = queryset.filter(pitches__semester=self.target_semester)
            self.is_seeking_members = True

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["is_seeking_members"] = self.is_seeking_members

        projects_data = []
        enrollments = Enrollment.objects.filter(
            project__in=self.get_queryset()
        ).select_related("user")
        if self.target_semester:
            enrollments = enrollments.filter(
                semester=self.target_semester
            ).select_related("semester")

        for project in self.get_queryset():
            project_data = {
                "project": project,
                "enrollments": len(
                    [e for e in enrollments if e.project_id == project.pk]
                ),
            }
            if self.target_semester:
                project_data["leads"] = [
                    e
                    for e in enrollments
                    if e.project_id == project.pk and e.is_project_lead == True
                ]
                project_data["pitch"] = next(
                    (
                        pitch
                        for pitch in project.pitches.all()
                        if pitch.semester_id == self.target_semester.pk
                    ),
                    None,
                )
            projects_data.append(project_data)

        data["projects_data"] = projects_data

        return data


class ProjectDetailView(SemesterFilteredDetailView):
    template_name = "portal/projects/detail.html"
    model = Project
    context_object_name = "project"

    def get_object(self, queryset=None):
        project: Project = super().get_object(queryset)
        if (
            not project.is_approved
            and not self.request.user.is_superuser
            and not self.request.user == project.owner
        ):
            raise Http404()
        return project

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if "target_semester" in data:
            data["target_semester_enrollments"] = Enrollment.objects.filter(
                semester=data["target_semester"], project=self.object
            ).order_by("-is_project_lead")
        else:
            enrollments_by_semester = {}
            for enrollment in self.object.enrollments.order_by(
                "-is_project_lead"
            ).all():
                if enrollment.semester not in enrollments_by_semester:
                    enrollments_by_semester[enrollment.semester] = []
                enrollments_by_semester[enrollment.semester].append(enrollment)
            data["enrollments_by_semester"] = enrollments_by_semester
        client = github.client_factory()
        
        try:
            data["repositories"] = [
                github.get_repository_details(client, repo.url)["repository"]
                for repo in self.object.repositories.all()
            ]
        except:
            data["repositories"] = []

        return data


class ProjectProposeView(
    SuccessMessageMixin, LoginRequiredMixin, UserRequiresSetupMixin, CreateView
):
    form_class = ProposeProjectForm
    template_name = "portal/projects/propose.html"
    success_message = "Your project has been proposed and will be reviwed by Mentors and Coordinators shortly."

    def get(self, request, *args, **kwargs):
        active_semester = Semester.get_active()
        if not self.request.user.can_propose_project(active_semester):
            messages.error(
                self.request, "You are not currently eligible to propose new projects."
            )
            return redirect(reverse("projects_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        active_semester = Semester.get_active()
        if not self.request.user.can_propose_project(active_semester):
            messages.error(
                self.request, "You are not currently eligible to propose new projects."
            )
            return redirect(reverse("projects_index"))

        form.instance.owner = self.request.user
        return super().form_valid(form)


class ProjectAddPitch(CreateView):
    model = ProjectPitch
    template_name = "portal/projects/pitch.html"
    fields = ["url"]
    success_url = "/"

    def get_context_data(self, **kwargs: Any):
        data = super().get_context_data(**kwargs)
        data["project"] = self.project
        data["semester"] = self.semester
        return data

    def get(self, request, *args: str, **kwargs: Any):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(pk=self.kwargs["slug"])
        if not self.project.owner == self.request.user:
            return HttpResponseForbidden()

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        self.semester = Semester.get_active()
        self.project = Project.objects.get(pk=self.kwargs["slug"])
        if not self.project.owner == self.request.user:
            return HttpResponseForbidden()

        form.instance.semester = self.semester
        form.instance.project = self.project
        return super().form_valid(form)
