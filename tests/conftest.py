import datetime as dt

import pytest
from django.core import management
from django.core.cache import caches
from django.utils.timezone import now
from django_scopes import scopes_disabled

from pretalx.event.domain.event import initialise_event
from pretalx.event.domain.plugins import enable_plugin
from pretalx.event.models import Event, Organiser, Team
from pretalx.person.models import User
from pretalx.schedule.models import Schedule

from pretalx_webhooks.models import WebhookSettings


@pytest.fixture(scope="session", autouse=True)
def collect_static():
    management.call_command("collectstatic", "--noinput", "--clear", verbosity=0)


@pytest.fixture(autouse=True)
def isolate_tests():
    with scopes_disabled():
        yield
    for cache in caches.all():
        cache.clear()


@pytest.fixture
def event():
    organiser = Organiser.objects.create(name="Test organiser", slug="organiser")
    today = dt.date.today()
    event = Event.objects.create(
        name="Test event",
        is_public=True,
        slug="test",
        email="orga@example.org",
        date_from=today,
        date_to=today,
        organiser=organiser,
    )
    initialise_event(event)
    enable_plugin(event, "pretalx_webhooks")
    return event


@pytest.fixture
def orga_user(event):
    user = User.objects.create_user(email="organiser@example.org", name="Organiser")
    team = Team.objects.create(
        name="Organisers",
        organiser=event.organiser,
        can_change_event_settings=True,
        can_change_submissions=True,
    )
    team.members.add(user)
    team.limit_events.add(event)
    return user


@pytest.fixture
def orga_client(orga_user, client):
    client.force_login(orga_user)
    return client


@pytest.fixture
def hook(event):
    return WebhookSettings.objects.create(
        event=event, url="https://example.org/hook", payload='{"action":"released"}'
    )


@pytest.fixture
def schedule(event):
    return Schedule.objects.create(event=event, version="1.0", published=now())
