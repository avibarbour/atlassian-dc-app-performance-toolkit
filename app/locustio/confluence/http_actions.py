import random
import re
import uuid

from locustio.common_utils import confluence_measure, fetch_by_re, timestamp_int,\
    TEXT_HEADERS, NO_TOKEN_HEADERS, logger, generate_random_string
from locustio.confluence.requests_params import confluence_datasets, Login, ViewPage, ViewDashboard, ViewBlog, \
    CreateBlog, CreateEditPage, CommentPage, UploadAttachments, LikePage

confluence_dataset = confluence_datasets()


@confluence_measure
def login_and_view_dashboard(locust):
    params = Login()

    user = random.choice(confluence_dataset["users"])
    username = user[0]
    password = user[1]

    login_body = params.login_body
    login_body['os_username'] = username
    login_body['os_password'] = password
    locust.client.post('/dologin.action', login_body, TEXT_HEADERS, catch_response=True)
    r = locust.client.get('/', catch_response=True)
    content = r.content.decode('utf-8')
    assert 'Log Out' in content, f'Login with {username}, {password} failed.'
    logger.info(f'User {username} is successfully logged in')
    keyboard_hash = fetch_by_re(params.keyboard_hash_re, content)
    build_number = fetch_by_re(params.build_number_re, content)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("010"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.get('/rest/mywork/latest/status/notification/count', catch_response=True)
    locust.client.get(f'/rest/shortcuts/latest/shortcuts/{build_number}/{keyboard_hash}', catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("025"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.get(f'/rest/experimental/search?cql=type=space%20and%20space.type=favourite%20order%20by%20favourite'
                      f'%20desc&expand=space.icon&limit=100&_={timestamp_int()}', catch_response=True)
    locust.client.get('/rest/dashboardmacros/1.0/updates?maxResults=40&tab=all&showProfilePic=true&labels='
                      '&spaces=&users=&types=&category=&spaceKey=', catch_response=True)
    locust.storage = dict()  # Define locust storage dict for getting cross-functional variables access
    locust.storage['build_number'] = build_number
    locust.storage['keyboard_hash'] = keyboard_hash
    locust.user = username


def view_page(locust):
    params = ViewPage()
    page = random.choice(confluence_dataset["pages"])
    page_id = page[0]

    @confluence_measure
    def view_page():
        r = locust.client.get(f'/pages/viewpage.action?pageId={page_id}', catch_response=True)
        content = r.content.decode('utf-8')
        assert 'Created by' and 'Save for later' in content, f'Fail to open page {page_id}'
        parent_page_id = fetch_by_re(params.parent_page_id_re, content)
        parsed_page_id = fetch_by_re(params.page_id_re, content)
        space_key = fetch_by_re(params.space_key_re, content)
        tree_request_id = fetch_by_re(params.tree_result_id_re, content)
        has_no_root = fetch_by_re(params.has_no_root_re, content)
        root_page_id = fetch_by_re(params.root_page_id_re, content)
        atl_token_view_issue = fetch_by_re(params.atl_token_view_issue_re, content)
        editable = fetch_by_re(params.editable_re, content)
        ancestor_ids = re.findall(params.ancestor_ids_re, content)

        ancestor_str = 'ancestors='
        for ancestor in ancestor_ids:
            ancestor_str = ancestor_str + str(ancestor) + '&'

        locust.storage['page_id'] = parsed_page_id
        locust.storage['has_no_root'] = has_no_root
        locust.storage['tree_request_id'] = tree_request_id
        locust.storage['root_page_id'] = root_page_id
        locust.storage['ancestors'] = ancestor_str
        locust.storage['space_key'] = space_key
        locust.storage['editable'] = editable
        locust.storage['atl_token_view_issue'] = atl_token_view_issue

        locust.client.get('/rest/helptips/1.0/tips', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("110"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/likes/1.0/content/{parsed_page_id}/likes?commentLikes=true&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/highlighting/1.0/panel-items?pageId={parsed_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageId={parsed_page_id}&_={timestamp_int()}',
                          catch_response=True)
        r = locust.client.get(f'/rest/inlinecomments/1.0/comments?containerId={parsed_page_id}&_={timestamp_int()}',
                              catch_response=True)
        content = r.content.decode('utf-8')
        assert 'authorDisplayName' or '[]' in content, f'Could not open comments for page {parsed_page_id}'
        locust.client.get(f'/plugins/editor-loader/editor.action?parentPageId={parent_page_id}&pageId={parsed_page_id}'
                          f'&spaceKey={space_key}&atl_after_login_redirect=/pages/viewpage.action'
                          f'&timeout=12000&_={timestamp_int()}', catch_response=True)
        locust.client.get(f'/rest/watch-button/1.0/watchState/{parsed_page_id}?_={timestamp_int()}',
                          catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("145"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("150"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("155"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("160"),
                           TEXT_HEADERS, catch_response=True)

    @confluence_measure
    def view_page_tree():
        tree_request_id = locust.storage['tree_request_id'].replace('&amp;', '&')
        ancestors = locust.storage['ancestors']
        root_page_id = locust.storage['root_page_id']
        viewed_page_id = locust.storage['page_id']
        space_key = locust.storage['space_key']
        r = ''
        # Page has parent
        if locust.storage['has_no_root'] == 'false':
            request = f"{tree_request_id}&hasRoot=true&pageId={root_page_id}&treeId=0&startDepth=0&mobile=false" \
                      f"&{ancestors}treePageId={viewed_page_id}&_={timestamp_int()}"
            r = locust.client.get(f'{request}', catch_response=True)
        # Page does not have parent
        elif locust.storage['has_no_root'] == 'true':
            request = f"{tree_request_id}&hasRoot=false&spaceKey={space_key}&treeId=0&startDepth=0&mobile=false" \
                      f"&{ancestors}treePageId={viewed_page_id}&_={timestamp_int()}"
            r = locust.client.get(f'{request}', catch_response=True)
        content = r.content.decode('utf-8')

        assert 'plugin_pagetree_children_span' and 'plugin_pagetree_children_list' in content

    view_page()
    view_page_tree()


@confluence_measure
def view_dashboard(locust):
    params = ViewDashboard()

    r = locust.client.get('/index.action', catch_response=True)
    content = r.content.decode('utf-8')
    keyboard_hash = fetch_by_re(params.keyboard_hash_re, content)
    build_number = fetch_by_re(params.build_number_re, content)
    assert 'quick-search' and 'Log Out' in content

    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("205"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.get('/rest/mywork/latest/status/notification/count', catch_response=True)
    locust.client.get(f'/rest/shortcuts/latest/shortcuts/{build_number}/{keyboard_hash}', catch_response=True)
    locust.client.get(f'/rest/experimental/search?cql=type=space%20and%20space.type=favourite%20order%20by%20'
                      f'favourite%20desc&expand=space.icon&limit=100&_={timestamp_int()}', catch_response=True)
    r = locust.client.get('/rest/dashboardmacros/1.0/updates?maxResults=40&tab=all&showProfilePic=true&labels='
                          '&spaces=&users=&types=&category=&spaceKey=', catch_response=True)
    assert 'changeSets' in r.content.decode('utf-8')


@confluence_measure
def view_blog(locust):
    params = ViewBlog()
    blog = random.choice(confluence_dataset["blogs"])
    blog_id = blog[0]

    r = locust.client.get(f'/pages/viewpage.action?pageId={blog_id}', catch_response=True)
    content = r.content.decode('utf-8')
    assert 'Created by' and 'Save for later' in content, f'Fail to open blog {blog_id}'

    parent_page_id = fetch_by_re(params.parent_page_id_re, content)
    parsed_blog_id = fetch_by_re(params.page_id_re, content)
    space_key = fetch_by_re(params.space_key_re, content)

    locust.client.get('/rest/helptips/1.0/tips', catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("310"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.get(f'/rest/likes/1.0/content/{parsed_blog_id}/likes?commentLikes=true&_={timestamp_int()}',
                      catch_response=True)
    locust.client.get(f'/rest/highlighting/1.0/panel-items?pageId={parsed_blog_id}&_={timestamp_int()}',
                      catch_response=True)
    locust.client.get(f'/rest/mywork/latest/status/notification/count?pageId={parsed_blog_id}&_={timestamp_int()}',
                      catch_response=True)
    r = locust.client.get(f'/rest/inlinecomments/1.0/comments?containerId={parsed_blog_id}&_={timestamp_int()}',
                          catch_response=True)
    content = r.content.decode('utf-8')
    assert 'authorDisplayName' or '[]' in content, f'Could not open comments for page {parsed_blog_id}'

    r = locust.client.get(f'/plugins/editor-loader/editor.action?parentPageId={parent_page_id}&pageId={parsed_blog_id}'
                          f'&spaceKey={space_key}&atl_after_login_redirect=/pages/viewpage.action'
                          f'&timeout=12000&_={timestamp_int()}', catch_response=True)
    assert 'draftId' in r.content.decode('utf-8'), f'Could not open editor for blog {parsed_blog_id}'

    locust.client.get(f'/rest/watch-button/1.0/watchState/{parsed_blog_id}?_={timestamp_int()}', catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("345"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("350"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("360"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("365"),
                       TEXT_HEADERS, catch_response=True)
    locust.client.get(f'/rest/quickreload/latest/{parsed_blog_id}?since={timestamp_int()}&_={timestamp_int()}',
                      catch_response=True)


def search_cql(locust):

    @confluence_measure
    def recently_viewed():
        locust.client.get('/rest/recentlyviewed/1.0/recent?limit=8', catch_response=True)

    @confluence_measure
    def search_results():
        r = locust.client.get(f'/rest/api/search?cql=siteSearch~{generate_random_string(2, only_letters=True)}'
                              f'&start=0&limit=20', catch_response=True)
        if '{"results":[' not in r.content.decode('utf-8'):
            logger.info(r.content.decode('utf-8'))
        assert '{"results":[' in r.content.decode('utf-8')
        locust.client.get('/rest/mywork/latest/status/notification/count', catch_response=True)

    recently_viewed()
    search_results()


def create_blog(locust):
    params = CreateBlog()
    blog = random.choice(confluence_dataset["blogs"])
    blog_space_key = blog[1]
    build_number = locust.storage.get('build_number', '')
    keyboard_hash = locust.storage.get('keyboard_hash', '')

    @confluence_measure
    def create_blog_editor():
        r = locust.client.get(f'/pages/createblogpost.action?spaceKey={blog_space_key}', catch_response=True)
        content = r.content.decode('utf-8')
        assert 'Blog post title' in content, f'Could not open editor for {blog_space_key}'

        atl_token = fetch_by_re(params.atl_token_re, content)
        content_id = fetch_by_re(params.content_id_re, content)
        parsed_space_key = fetch_by_re(params.space_key, content)

        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("910"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageId=0', catch_response=True)
        locust.client.get('/plugins/servlet/notifications-miniview', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("925"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("930"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/emoticons/1.0/_={timestamp_int()}', catch_response=True)
        locust.client.get(f'/rest/shortcuts/latest/shortcuts/{build_number}/{keyboard_hash}?_={timestamp_int()}',
                          catch_response=True)

        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": content_id,
                                   "draftType": "blogpost",
                                   "spaceKey": parsed_space_key,
                                   "atl_token": atl_token
                                   }
        r = locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                               TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert atl_token in content

        contributor_hash = fetch_by_re(params.contribution_hash, content)
        locust.storage['contributor_hash'] = contributor_hash

        r = locust.client.get(f'/rest/ui/1.0/content/{content_id}/labels', catch_response=True)
        assert '"success":true' in r.content.decode('utf-8'), f'Could not get labels for content {content_id}'

        draft_name = f"Performance Blog - {generate_random_string(10, only_letters=True)}"
        locust.storage['draft_name'] = draft_name
        locust.storage['parsed_space_key'] = parsed_space_key
        locust.storage['content_id'] = content_id
        locust.storage['atl_token'] = atl_token

        draft_body = {"draftId": content_id,
                      "pageId": "0",
                      "type": "blogpost",
                      "title": draft_name,
                      "spaceKey": parsed_space_key,
                      "content": "<p>test blog draft</p>",
                      "syncRev": "0.mcPCPtDvwoayMR7zvuQSbf8.27"}

        TEXT_HEADERS['Content-Type'] = 'application/json'
        r = locust.client.post('/rest/tinymce/1/drafts', json=draft_body, headers=TEXT_HEADERS, catch_response=True)
        assert 'draftId' in r.content.decode('utf-8'), f'Could not create blogpost draft in space {parsed_space_key}'

    @confluence_measure
    def create_blog():
        draft_name = locust.storage['draft_name']
        parsed_space_key = locust.storage['parsed_space_key']
        content_id = locust.storage['content_id']
        atl_token = locust.storage['atl_token']

        draft_body = {"status": "current", "title": draft_name, "space": {"key": f"{parsed_space_key}"},
                      "body": {"editor": {"value": f"Test Performance Blog Page Content {draft_name}",
                                          "representation": "editor", "content": {"id": f"{content_id}"}}},
                      "id": f"{content_id}", "type": "blogpost",
                      "version": {"number": 1, "minorEdit": True, "syncRev": "0.mcPCPtDvwoayMR7zvuQSbf8.30"}}
        TEXT_HEADERS['Content-Type'] = 'application/json'
        r = locust.client.put(f'/rest/api/content/{content_id}?status=draft', json=draft_body,
                              headers=TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert 'current' and 'title' in content, f'Could not open draft {draft_name} in space {parsed_space_key}'
        created_blog_title = fetch_by_re(params.created_blog_title_re, content)
        logger.info(f'Blog {created_blog_title} created')

        r = locust.client.get(f'/{created_blog_title}', catch_response=True)
        assert 'Created by' in r.content.decode('utf-8'), f'Could not open created blog {created_blog_title}'

        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("970"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("975"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get('/plugins/servlet/notifications-miniview', catch_response=True)
        locust.client.get(f'/rest/watch-button/1.0/watchState/{content_id}?_={timestamp_int()}', catch_response=True)
        locust.client.get(f'/rest/likes/1.0/content/{content_id}/likes?commentLikes=true&_={timestamp_int()}',
                          catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("995"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/highlighting/1.0/panel-items?pageId={content_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/inlinecomments/1.0/comments?containerId={content_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/s/en_GB/{build_number}/{keyboard_hash}/_/images/icons/profilepics/add_profile_pic.svg',
                          catch_response=True)
        locust.client.get('/rest/helptips/1.0/tips', catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageid={content_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/plugins/editor-loader/editor.action?parentPageId=&pageId={content_id}'
                          f'&spaceKey={parsed_space_key}&atl_after_login_redirect={created_blog_title}'
                          f'&timeout=12000&_={timestamp_int()}', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1030"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1035"),
                           TEXT_HEADERS, catch_response=True)

        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": content_id,
                                   "draftType": "blogpost",
                                   "spaceKey": parsed_space_key,
                                   "atl_token": atl_token
                                   }
        r = locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                               TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert atl_token in content

    create_blog_editor()
    create_blog()


def create_and_edit_page(locust):
    params = CreateEditPage()
    page = random.choice(confluence_dataset["pages"])
    page_id = page[0]
    space_key = page[1]
    build_number = locust.storage.get('build_number', '')
    keyboard_hash = locust.storage.get('keyboard_hash', '')

    @confluence_measure
    def create_page_editor():
        r = locust.client.get(f'/pages/createpage.action?spaceKey={space_key}&fromPageId={page_id}&src=quick-create',
                              catch_response=True)
        content = r.content.decode('utf-8')
        assert 'Page Title' in content

        parsed_space_key = fetch_by_re(params.space_key_re, content)
        atl_token = fetch_by_re(params.atl_token_re, content)
        content_id = fetch_by_re(params.content_id_re, content)
        locust.storage['content_id'] = content_id
        locust.storage['atl_token'] = atl_token

        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("705"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("710"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("715"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get('/rest/create-dialog/1.0/storage/quick-create', catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageid=0&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/jiraanywhere/1.0/servers?_={timestamp_int()}', catch_response=True)
        locust.client.get(f'/rest/shortcuts/latest/shortcuts/{build_number}/{keyboard_hash}', catch_response=True)
        locust.client.get(f'/rest/emoticons/1.0/?_={timestamp_int()}', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("750"),
                           TEXT_HEADERS, catch_response=True)

        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": content_id,
                                   "draftType": "page",
                                   "spaceKey": parsed_space_key,
                                   "atl_token": atl_token
                                   }
        r = locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                               TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert atl_token in content

    @confluence_measure
    def create_page():
        draft_name = f"{generate_random_string(10, only_letters=True)}"
        content_id = locust.storage['content_id']
        atl_token = locust.storage['atl_token']
        create_page_body = {
                            "status": "current",
                            "title": f"Test Performance JMeter {draft_name}",
                            "space": {"key": f"{space_key}"},
                            "body": {
                              "storage": {
                                "value": f"Test Performance Create Page Content {draft_name}",
                                "representation": "storage",
                                "content": {
                                  "id": f"{content_id}"
                                }
                              }
                            },
                            "id": f"{content_id}",
                            "type": "page",
                            "version": {
                              "number": 1
                            },
                            "ancestors": [
                              {
                                "id": f"{page_id}",
                                "type": "page"
                              }
                            ]
                        }

        TEXT_HEADERS['Content-Type'] = 'application/json'
        TEXT_HEADERS['X-Requested-With'] = 'XMLHttpRequest'
        r = locust.client.put(f'/rest/api/content/{content_id}?status=draft', json=create_page_body,
                              headers=TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert 'draftId' in content, f'Could not create PAGE draft in space {space_key}'
        page_title = fetch_by_re(params.page_title_re, content)

        r = locust.client.get(f'{page_title}', catch_response=True)
        content = r.content.decode('utf-8')
        assert 'Created by' in content, f'Page {page_title} is not created'

        parent_page_id = fetch_by_re(params.parent_page_id, content)
        create_page_id = fetch_by_re(params.create_page_id, content)
        locust.storage['create_page_id'] = create_page_id
        locust.storage['parent_page_id'] = parent_page_id

        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": content_id,
                                   "space_key": space_key,
                                   "draftType": "page",
                                   "atl_token": atl_token
                                   }
        locust.client.post('/json/stopheartbeatactivity.action', params=heartbeat_activity_body,
                           headers=TEXT_HEADERS, catch_response=True)

        locust.client.get(f'/rest/helptips/1.0/tips', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("795"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/jira-metadata/1.0/metadata/aggregate?pageId={create_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/likes/1.0/content/{create_page_id}/likes?commentLikes=true&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/inlinecomments/1.0/comments?containerId={create_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageid={create_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/highlighting/1.0/panel-items?pageId={create_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/watch-button/1.0/watchState/{create_page_id}?_={timestamp_int()}',
                          catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("830"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("835"),
                           TEXT_HEADERS, catch_response=True)

        r = locust.client.get(f'/plugins/editor-loader/editor.action?parentPageId={parent_page_id}'
                              f'&pageId={create_page_id}&spaceKey={space_key}'
                              f'&atl_after_login_redirect={page_title}&timeout=12000&_={timestamp_int()}',
                              catch_response=True)
        assert page_title in r.content.decode('utf-8'), f'Editor loader failed in space {space_key}. Page {page_title}'

        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("845"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("850"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("855"),
                           TEXT_HEADERS, catch_response=True)

    @confluence_measure
    def open_editor():
        create_page_id = locust.storage['create_page_id']

        r = locust.client.get(f'/pages/editpage.action?pageId={create_page_id}', catch_response=True)
        content = r.content.decode('utf-8')
        assert '<title>Edit' and 'Update</button>' in content, f'Could not open PAGE {create_page_id} to edit'

        edit_page_version = fetch_by_re(params.editor_page_version_re, content)
        edit_atl_token = fetch_by_re(params.atl_token_re, content)
        edit_space_key = fetch_by_re(params.space_key_re, content)
        edit_content_id = fetch_by_re(params.content_id_re, content)
        edit_page_id = fetch_by_re(params.page_id_re, content)
        edit_parent_page_id = fetch_by_re(params.parent_page_id, content)

        locust.storage['edit_parent_page_id'] = edit_parent_page_id
        locust.storage['edit_page_version'] = edit_page_version
        locust.storage['edit_page_id'] = edit_page_id
        locust.storage['atl_token'] = edit_atl_token

        locust.client.get(f'/rest/jiraanywhere/1.0/servers?_={timestamp_int()}', catch_response=True)
        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": edit_content_id,
                                   "draftType": "page",
                                   "spaceKey": edit_space_key,
                                   "atl_token": edit_atl_token
                                   }
        locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                           TEXT_HEADERS, catch_response=True)
        expand = 'history.createdBy.status%2Chistory.contributors.publishers.users.status' \
                 '%2Cchildren.comment.version.by.status'
        locust.client.get(f'/rest/api/content/{edit_page_id}?expand={expand}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/emoticons/1.0/_={timestamp_int()}', catch_response=True)
        locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/ui/1.0/content/{edit_page_id}/labels?_={timestamp_int()}', catch_response=True)
        locust.client.get('/rest/mywork/latest/status/notification/count', catch_response=True)
        locust.client.post('/json/startheartbeatactivity.action', heartbeat_activity_body,
                           TEXT_HEADERS, catch_response=True)

    @confluence_measure
    def edit_page():
        draft_name = f"{generate_random_string(10, only_letters=True)}"
        edit_parent_page_id = locust.storage['edit_parent_page_id']
        edit_page_id = locust.storage['edit_page_id']
        content_id = locust.storage['content_id']
        edit_page_version = int(locust.storage['edit_page_version']) + 1
        edit_atl_token = locust.storage['atl_token']
        edit_page_body = dict()

        if edit_parent_page_id:
            edit_page_body = {
                  "status": "current",
                  "title": f"Test Performance Edit with locust {draft_name}",
                  "space": {
                    "key": f"{space_key}"
                  },
                  "body": {
                    "storage": {
                      "value": f"Page edit with locust {draft_name}",
                      "representation": "storage",
                      "content": {
                        "id": f"{content_id}"
                      }
                    }
                  },
                  "id": f"{content_id}",
                  "type": "page",
                  "version": {
                    "number": f"{edit_page_version}"
                  },
                  "ancestors": [
                    {
                      "id": f"{edit_parent_page_id}",
                      "type": "page"
                    }
                  ]
                }

        if not edit_parent_page_id:
            edit_page_body = {
                              "status": "current",
                              "title": f"Test Performance Edit with JMeter {draft_name}",
                              "space": {
                                "key": f"{space_key}"
                              },
                              "body": {
                                "storage": {
                                  "value": f"Page edit with JMeter {draft_name}",
                                  "representation": "storage",
                                  "content": {
                                    "id": f"{content_id}"
                                  }
                                }
                              },
                              "id": f"{content_id}",
                              "type": "page",
                              "version": {
                                "number": f"{edit_page_version}"
                              }
                            }
        TEXT_HEADERS['Content-Type'] = 'application/json'
        TEXT_HEADERS['X-Requested-With'] = 'XMLHttpRequest'
        r = locust.client.put(f'/rest/api/content/{content_id}?status=draft', json=edit_page_body,
                              headers=TEXT_HEADERS, catch_response=True)
        content = r.content.decode('utf-8')
        assert f'"title":"Test Performance Edit with locust {draft_name}"' in content, \
            f'User {locust.user} could not edit page {content_id}, parent page id: {edit_parent_page_id}'

        r = locust.client.get(f'/pages/viewpage.action?pageId={edit_page_id}', catch_response=True)
        assert 'last-modified' and 'Created by' in r.content.decode('utf-8'),\
            f'Could not open page {edit_page_id}, name: Test Performance Edit with locust {draft_name}'

        locust.client.get('/rest/mywork/latest/status/notification/count', catch_response=True)
        heartbeat_activity_body = {"dataType": "json",
                                   "contentId": content_id,
                                   "space_key": space_key,
                                   "draftType": "page",
                                   "atl_token": edit_atl_token
                                   }
        locust.client.post('/json/stopheartbeatactivity.action', params=heartbeat_activity_body,
                           headers=TEXT_HEADERS, catch_response=True)
        locust.client.get('/rest/helptips/1.0/tips', catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1175"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.get(f'/rest/jira-metadata/1.0/metadata/aggregate?pageId={edit_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/likes/1.0/content/{edit_page_id}/likes?commentLikes=true&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/highlighting/1.0/panel-items?pageId={edit_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/mywork/latest/status/notification/count?pageId={edit_page_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/plugins/editor-loader/editor.action?parentPageId={edit_parent_page_id}'
                          f'&pageId={edit_page_id}&spaceKey={space_key}&atl_after_login_redirect=/pages/viewpage.action'
                          f'&timeout=12000&_={timestamp_int()}', catch_response=True)
        locust.client.get(f'/rest/inlinecomments/1.0/comments?containerId={content_id}&_={timestamp_int()}',
                          catch_response=True)
        locust.client.get(f'/rest/watch-button/1.0/watchState/{edit_page_id}?_={timestamp_int()}',
                          catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1215"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1220"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1225"),
                           TEXT_HEADERS, catch_response=True)
        locust.client.post('/rest/webResources/1.0/resources', params.resources_body.get("1230"),
                           TEXT_HEADERS, catch_response=True)

    create_page_editor()
    create_page()
    open_editor()
    edit_page()


@confluence_measure
def comment_page(locust):
    page = random.choice(confluence_dataset["pages"])
    page_id = page[0]
    comment = f'<p>{generate_random_string(length=15, only_letters=True)}</p>'
    uid = str(uuid.uuid4())
    r = locust.client.post(f'/rest/tinymce/1/content/{page_id}/comment?actions=true',
                           params={'html': comment, 'watch': True, 'uuid': uid}, headers=NO_TOKEN_HEADERS,
                           catch_response=True)
    assert 'reply-comment' and 'edit-comment' in r.content.decode('utf-8'), 'Could not add comment'


@confluence_measure
def view_attachments(locust):
    page = random.choice(confluence_dataset["pages"])
    page_id = page[0]
    r = locust.client.get(f'/pages/viewpageattachments.action?pageId={page_id}', catch_response=True)
    assert 'Upload file' and 'Attach more files' and 'Download All' \
           or 'currently no attachments' in r.content.decode('utf-8')


@confluence_measure
def upload_attachments(locust):
    params = UploadAttachments()
    page = random.choice(confluence_dataset["pages"])
    static_content = random.choice(confluence_dataset["static-content"])
    file_path = static_content[0]
    file_name = static_content[2]
    file_extension = static_content[1]
    page_id = page[0]

    r = locust.client.get(f'/pages/viewpage.action?pageId={page_id}', catch_response=True)
    content = r.content.decode('utf-8')
    assert 'Created by' and 'Save for later' in content, f'Fail to open page {page_id}'
    atl_token_view_issue = fetch_by_re(params.atl_token_view_issue_re, content)

    multipart_form_data = {
        "file": (file_name, open(file_path, 'rb'), file_extension)
    }

    r = locust.client.post(f'/pages/doattachfile.action?pageId={page_id}',
                           params={"atl_token": atl_token_view_issue, "comment_0": "", "comment_1": "", "comment_2": "",
                                   "comment_3": "", "comment_4": "0", "confirm": "Attach"}, files=multipart_form_data,
                           catch_response=True)
    content = r.content.decode('utf-8')
    assert 'Upload file' and 'Attach more files' in content, 'Could not upload attachments'


@confluence_measure
def like_page(locust):
    params = LikePage()
    page = random.choice(confluence_dataset["pages"])
    page_id = page[0]

    r = locust.client.get(f'/rest/likes/1.0/content/{page_id}/likes?commentLikes=true&_={timestamp_int()}',
                          catch_response=True)
    content = r.content.decode('utf-8')
    like = fetch_by_re(params.like_re, content)
    TEXT_HEADERS['Content-Type'] = 'application/json'

    if like:
        r = locust.client.delete(f'/rest/likes/1.0/content/{page_id}/likes', catch_response=True)
    if not like:
        r = locust.client.post(f'/rest/likes/1.0/content/{page_id}/likes', TEXT_HEADERS, catch_response=True)
    if 'likes' not in r.content.decode('utf-8'):
        logger.info(str(r))
    assert 'likes' in r.content.decode('utf-8'), f'Could not set like to the page {page_id}'
