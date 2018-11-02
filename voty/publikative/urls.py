from django.conf.urls import url, include

from pinax.teams import views
from django.conf.urls import url

from pinax.blog.conf import settings
from pinax.blog.views import (
    BlogIndexView,
    DateBasedPostDetailView,
    ManageCreatePost,
    ManageDeletePost,
    ManagePostList,
    ManageUpdatePost,
    SecretKeyPostDetailView,
    SectionIndexView,
    SlugUniquePostDetailView,
    StaffPostDetailView,
    ajax_preview,
    blog_feed,
)

app_name = "pub"

teams_general = [
    url(r"^$", views.TeamListView.as_view(), name="team_list"),
    url(r"^:create/$", views.TeamCreateView.as_view(), name="team_create"),
    url(r"^:accept/(?P<pk>\d+)/$", views.team_accept, name="team_accept"),
    url(r"^:reject/(?P<pk>\d+)/$", views.team_reject, name="team_reject"),
]

blog_general = [
    url(r"^r/(?P<section>[-\w]+)/$", SectionIndexView.as_view(), name="blog_section"),
    url(r"^f/(?P<section>[-\w]+)/(?P<feed_type>[-\w]+)/$", blog_feed, name="blog_feed"),
]

team_blog = [
    url(r"^$", BlogIndexView.as_view(), name="show"),
    url(r"^post/(?P<post_pk>\d+)/$", StaffPostDetailView.as_view(), name="blog_post_pk"),
    url(r"^post/(?P<post_secret_key>\w+)/$", SecretKeyPostDetailView.as_view(), name="blog_post_secret"),

    # authoring
    url(r"^manage/posts/$", ManagePostList.as_view(), name="manage_post_list"),
    url(r"^manage/posts/:create/$", ManageCreatePost.as_view(), name="manage_post_create"),
    url(r"^manage/posts/(?P<post_pk>\d+)/:update/$", ManageUpdatePost.as_view(), name="manage_post_update"),
    url(r"^manage/posts/(?P<post_pk>\d+)/:delete/$", ManageDeletePost.as_view(), name="manage_post_delete"),

    url(r"^ajax/markdown/preview/$", ajax_preview, name="ajax_preview"),
    url(r"^(?P<post_slug>[-\w]+)/$", SlugUniquePostDetailView.as_view(), name="blog_post_slug")
]

team_actions = [
    # team specific
    url(r"^(?P<slug>[\w\-]+)/:join/$", views.team_join, name="team_join"),
    url(r"^(?P<slug>[\w\-]+)/:leave/$", views.team_leave, name="team_leave"),
    url(r"^(?P<slug>[\w\-]+)/:apply/$", views.team_apply, name="team_apply"),
    url(r"^(?P<slug>[\w\-]+)/:edit/$", views.team_update, name="team_edit"),
    url(r"^(?P<slug>[\w\-]+)/:manage/$", views.TeamManageView.as_view(), name="team_manage"),

    # membership specific
    url(r"^(?P<slug>[\w\-]+)/:ac/users-to-invite/$", views.autocomplete_users, name="team_autocomplete_users"),  # noqa
    url(r"^(?P<slug>[\w\-]+)/:invite-user/$", views.TeamInviteView.as_view(), name="team_invite"),
    url(r"^(?P<slug>[\w\-]+)/members/(?P<pk>\d+)/:revoke-invite/$", views.team_member_revoke_invite, name="team_member_revoke_invite"),  # noqa
    url(r"^(?P<slug>[\w\-]+)/members/(?P<pk>\d+)/:resend-invite/$", views.team_member_resend_invite, name="team_member_resend_invite"),  # noqa
    url(r"^(?P<slug>[\w\-]+)/members/(?P<pk>\d+)/:promote/$", views.team_member_promote, name="team_member_promote"),  # noqa
    url(r"^(?P<slug>[\w\-]+)/members/(?P<pk>\d+)/:demote/$", views.team_member_demote, name="team_member_demote"),  # noqa
    url(r"^(?P<slug>[\w\-]+)/members/(?P<pk>\d+)/:remove/$", views.team_member_remove, name="team_member_remove"),  # noqa
]

urlpatterns = [
    url(r"^teams/", 
        include((teams_general, "pinax_teams"), namespace="teams")),
    url(r"^@(?P<slug>[\w\-]+)/",
        include((team_actions, "pinax_teams"), namespace="teams")),
    url(r"^@(?P<slug>[\w\-]+)/",
        include((team_blog, "pinax_blog"), namespace="blog")),
    url(r'', include(blog_general))
]
