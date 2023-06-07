# coding: utf-8

"""
    Titan API v1

    # Introduction The Intel 471 API is organized around the principles of REST. Our API lets you gather results from our platform using anything that can send a HTTP request, including cURL and modern internet browsers. Access to this API requires an API token which is managed from your account settings.  Intel 471 reserves the right to add fields to our API however we will provide backwards compatibility and older version support so that it will be possible to choose exact versions that provide a response with an older structure.  # Authentication Authentication to the API occurs by providing your email address as the login and API key as a password in the authorization header via HTTP Basic Auth. Your API key can be found in the [API](https://portal.intel471.com/api) section on the portal. It carries many privileges so please do not expose it on public web resources.  # Accessing the API  Following examples demonstrate different methods to get the reports from `/reports` endpoint.  ## Internet browser  Just open URL: https://api.intel471.com/v1/reports  Browser will ask you for credentials, provide your email as login and API key as password.  ## cURL command line utility  Execute following command in your terminal:  ``` curl -u <YOU EMAIL>:<YOUR API KEY> https://api.intel471.com/v1/reports ```  ## Python client  We provide a [Python client](https://github.com/intel471/titan-client-python) for Intel 471's Titan API, which aims at providing common ground for all the endpoints. Please note that all the call parameters and response body fields' names are normalized to camel_case, so for example when you search reports by document type using Python client use `document_type` instead of `documentType`.  Install the client using pip (python >= 3.6 required):  ``` pip install titan-client ```  Run following script  ```python import titan_client  configuration = titan_client.Configuration(     username=\"<YOU EMAIL>\",     password=\"<YOUR API KEY>\")  with titan_client.ApiClient(configuration) as api_client:     api_instance = titan_client.ReportsApi(api_client)     api_response = api_instance.reports_get() print(api_response) ```  # Use cases  Below we present several commonly used scenarios in both raw HTTP request format and as a script using Python client. Examples are simplified so that they do not contain the authentication part and for Python client they do not contain configuration and API client object creation portion. For full example please refer to **Accessing the API** section of this document.   ## Paging  One page of the results can carry up to 100 records and you can display up to 11 pages for one query (max offset is 1000) in non-stream API endpoints. Use `count` parameter to set the number of items per page. Use `offset` parameter to shift the window by given number of results.       **HTTP**   ``` # Get 20 reports, sorted by the default field GET https://api.intel471.com/v1/reports?count=20  # Get next 20 reports GET https://api.intel471.com/v1/reports?count=20&offset=20  # Get 40 reports in one go to save API calls GET https://api.intel471.com/v1/reports?count=40 ```  **Python**  ``` response = titan_client.ReportsApi(api_client).reports_get(count=20, offset=20) ```  ## Paging beyond the max allowed offset  Paging described in the previous use case is generally sufficient for most needs. If there are more than 1100 objects  to be obtained for a given time period and set of filter criteria, then it is possible to move the filter timestamps  along and then restart the offset sequencing. There is a very small number of situations where this may cause issues,  where there is multiple objects with the same timestamp adjacent to the last object in the response.  For the higher volume or fast changing data (such as malware indicators, malware events, creds) there are stream API endpoints  available where cursors may be used in order to acquire data easily and to avoid the need to shift timestamp ranges.  ``` # Get first 11 pages, 100 objects each  GET https://api.intel471.com/v1/reports?sort=latest&count=100 GET https://api.intel471.com/v1/reports?sort=latest&count=100&offset=100 ... GET https://api.intel471.com/v1/reports?sort=latest&count=100&offset=1000 ... > {\"reports\": [{..., \"created\": 1661867086000}, {..., \"created\": 1661864268000}]} ```  Then the `created` time value from the last response will be used as an upper limit in the next series of calls:  ```   GET https://api.intel471.com/v1/reports?sort=latest&until=1661864268000&count=100 GET https://api.intel471.com/v1/reports?sort=latest&until=1661864268000&offset=100 ... GET https://api.intel471.com/v1/reports?sort=latest&until=1661864268000&offset=1000 ```  And so on, until the results are available or until the desired number of objects has been fetched.  ## Paging /alerts endpoint  Alerts endpoint differs from all the other non-stream API endpoints in that the `offset` parameter needs to be set  to the uid of the most recent acquired alert instead of an integer indicating the shift.  **HTTP**   ``` GET https://api.intel471.com/v1/alerts?count=100 > {\"alerts\": [{..., \"uid\": \"abc123\"}, {..., \"uid\": \"abc234\"}]}  GET https://api.intel471.com/v1/alerts?count=100&offset=abc234 > {\"alerts\": [{..., \"uid\": \"abc345\"}, {..., \"uid\": \"abc456\"}]} ```  **Python**  ``` response = titan_client.AlertsApi(api_client).alerts_get(count=100, offset=\"abc456\") ```  ## Stream endpoints paging  Stream endpoints provide the same data as their regular counterparts but they differ in a way of paging.  When working with a stream endpoint, the response always contains `cursorNext` field, which should be provided to the next subsequent  call to fetch potential next page of the results. All the subsequent calls should have the same set of query parameters as the first one,  except the cursor value. Keep calling the endpoint with a new cursor value until it stops yielding results. When new data appear after that, another call will fetch it.  **HTTP**   ``` GET https://api.intel471.com/v1/indicators/stream?lastUpdatedFrom=1655809200000 > {\"indicators\": [...], \"cursorNext\": \"MTY1NT1\"}  GET https://api.intel471.com/v1/indicators/stream?lastUpdatedFrom=1655809200000&cursor=MTY1NT1 > {\"indicators\": [...], \"cursorNext\": \"MTY1NT2\"}  GET https://api.intel471.com/v1/indicators/stream?lastUpdatedFrom=1655809200000&cursor=MTY1NT2 > {\"cursorNext\": \"MTY1NT3\"} ```  **Python**  ``` response = titan_client.IndicatorsApi(api_client).indicators_stream_get(last_updated_from=1656809200000) print(response.cursor_next, response.indicators) # MTY1NT1, [...]  response = titan_client.IndicatorsApi(api_client).indicators_stream_get(last_updated_from=1656809200000, cursor=\"MTY1NT1\")) print(response.cursor_next, response.indicators) # MTY1NT2, [...]  response = titan_client.IndicatorsApi(api_client).indicators_stream_get(last_updated_from=1656809200000, cursor=\"MTY1NT2\")) print(response.cursor_next, response.indicators) # MTY1NT3, None ```  ## Querying using logical operators  ### Array parameters  Any query parameter can be singular or array, if multiple parameters with the same name were provided. All parameters with the same name are internally combined into a query with `AND` operator.  So following query:  ``` GET https://api.intel471.com/v1/reports?report=sources&report=abba ```  Means \"find me reports with `source` AND `abba` in their body\".  This approach is not supported in the Python client. Instead use query string method discussed below.   ### Query string parameters  Query parameters accept Elastic's query string syntax, which allows for even better flexibility.  For example above query can be rephrased as:  **HTTP**   ``` GET https://api.intel471.com/v1/reports?report=sources OR abba ```  **Python**  ``` response = titan_client.ReportsApi(api_client).reports_get(report=\"sources OR abba\") ```  More advanced combination would include both `OR` and `AND` operators and a negation:  **HTTP**  ``` GET https://api.intel471.com/v1/reports?report=(sources OR abba) AND -creaba ```  **Python**  ``` response = titan_client.ReportsApi(api_client).reports_get(report=\"(sources OR abba) AND -creaba\") ```  Means \"find me reports with `source` or `abba` in their body which at the same time do not contain `creaba`\".  The query string \"mini-language\" reference and examples can be found on  [Elastic's query string syntax](https://www.elastic.co/guide/en/elasticsearch/reference/7.5/query-dsl-query-string-query.html#query-dsl-query-string-query) page.  ## Get CVEs using multiple filtering criteria  Get all CVE reports for Chrome product where the risk is high and the patch is not available yet.  **HTTP**   ``` GET https://api.intel471.com/v1/cve/reports?productName=Chrome&riskLevel=high&patchStatus=unavailable ```  **Python**  ``` response = titan_client.VulnerabilitiesApi(api_client).cve_reports_get(     product_name=\"Chrome\",     risk_level=\"high\",     patch_status=\"unavailable\" ) ```  ## List watcher groups   **HTTP**   ``` GET https://api.intel471.com/v1/watcherGroups ```  **Python**  ``` response = titan_client.WatchersApi(api_client).watcher_groups_get() ```  ## Create watcher group   To create a watcher group you need to pass a body along with the request.  **HTTP**   ``` POST https://api.intel471.com/v1/watcherGroups {   \"name\": \"my_group_name\",   \"description\": \"My description\" } ```  **Python**  ``` response = titan_client.WatchersApi(api_client).watcher_groups_post(   {\"name\": \"my_group_name\", \"description\": \"My description\"} ) ```  ## Create free text search watcher  **HTTP**   ``` POST https://api.intel471.com/v1/watcherGroups/<GROUP UID>/watchers {   \"type\": \"search\",   \"freeTextPattern\": \"text to search\",   \"notificationChannel\": \"website\" } ```  **Python**  ``` response = titan_client.WatchersApi(api_client).watcher_groups_group_uid_watchers_post(   group_uid=\"<GROUP UID>\",   watcher_request_body_post={     \"type\": \"search\",     \"freeTextPattern\": \"text to search\",     \"notificationChannel\": \"website\"   } ) ```  ## Create specific search watcher  **HTTP**   ``` POST https://api.intel471.com/v1/watcherGroups/<GROUP UID>/watchers {   \"type\": \"search\",   \"patterns\": [     {\"types\": \"Actor\" , \"pattern\": \"swisman\"}   ],   \"notificationChannel\": \"website\" } ```  **Python**  ``` response = titan_client.WatchersApi(api_client).watcher_groups_group_uid_watchers_post(   group_uid=\"<GROUP UID>\",   watcher_request_body_post={     \"type\": \"search\",     \"patterns\": [       {\"types\": \"Actor\" , \"pattern\": \"swisman\"}     ],     \"notificationChannel\": \"website\"   } ) ```  # API integration best practice with your application CORS requests to the API are not allowed due to security concerns, so please avoid AJAX calls directly from the browser. Instead consider setting up a server side proxy in your application to handle API requests.  Please consider not storing information provided by the API locally as we are constantly improving our data set and want you to have the most updated information.  # Versioning support We consistently improve our API and occasionally introduce the changes based on the customer feedback. The current API version is provided in this documentation's header. We provide API backwards compatibility whenever possible.  All requests are prefixed with the major version number, for example `/v1`:  ``` https://api.intel471.com/v1/reports ```  Different major versions are not compatible and imply significant response structure changes. Minor versions differences might include extra fields in response or provide new request parameter support. To stick to the specific version, just add `v` parameter to the request, for example: `?v=1.19.2`. If you specify a non existing version, it will be brought down to the nearest existing one.  Omitting the version parameter in the request will call the latest version of the API.  We consistently phase out the outdated versions of the API, keeping only several most recent versions. Specific version is getting disabled only when we do not record any requests using it, so it's guaranteed that calls to the outdated ones will work, though we recommend switching to the latest one as soon as possible.  We recommend to always add the version parameter to the request to be safe on API updates in your integrations.   Python client always adds the version parameter in the underlying request. API version matches the Python client's package version.   # noqa: E501

    The version of the OpenAPI document: 1.19.7
    Generated by: https://openapi-generator.tech
"""


from __future__ import absolute_import

import re  # noqa: F401

# python 2 and python 3 compatibility library
import six

from titan_client.api_client import ApiClient
from titan_client.exceptions import (  # noqa: F401
    ApiTypeError,
    ApiValueError
)


class WatchersApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client

    def watcher_groups_get(self, **kwargs):  # noqa: E501
        """Get Watcher Group List  # noqa: E501

        Returns list of Watcher groups matching filter criteria.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_get(async_req=True)
        >>> result = thread.get()

        :param section: Shows watcher groups from defined section.
        :type section: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: WatcherGroupResponse
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_get_with_http_info(**kwargs)  # noqa: E501

    def watcher_groups_get_with_http_info(self, **kwargs):  # noqa: E501
        """Get Watcher Group List  # noqa: E501

        Returns list of Watcher groups matching filter criteria.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_get_with_http_info(async_req=True)
        >>> result = thread.get()

        :param section: Shows watcher groups from defined section.
        :type section: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(WatcherGroupResponse, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'section'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_get" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']

        collection_formats = {}

        path_params = {}

        query_params = []
        if local_var_params.get('section') is not None:  # noqa: E501
            query_params.append(('section', local_var_params['section']))  # noqa: E501

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "WatcherGroupResponse",
        }

        return self.api_client.call_api(
            '/watcherGroups', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_delete(self, group_uid, **kwargs):  # noqa: E501
        """Delete Watcher Group  # noqa: E501

        Delete defined watcher group. Only groups of type owned_by_me are allowed to be deleted.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_delete(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_delete_with_http_info(group_uid, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_delete_with_http_info(self, group_uid, **kwargs):  # noqa: E501
        """Delete Watcher Group  # noqa: E501

        Delete defined watcher group. Only groups of type owned_by_me are allowed to be deleted.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_delete_with_http_info(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        local_var_params = locals()

        all_params = [
            'group_uid'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_delete" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_delete`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['text/plain'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {}

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}', 'DELETE',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_get(self, group_uid, **kwargs):  # noqa: E501
        """Get Watcher Group  # noqa: E501

        Get a watcher group by UID.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_get(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: SimpleWatcherGroupSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_get_with_http_info(group_uid, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_get_with_http_info(self, group_uid, **kwargs):  # noqa: E501
        """Get Watcher Group  # noqa: E501

        Get a watcher group by UID.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_get_with_http_info(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(SimpleWatcherGroupSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'group_uid'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_get" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_get`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "SimpleWatcherGroupSchema",
            404: "str",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_put(self, group_uid, watcher_groups_group_uid_put_request, **kwargs):  # noqa: E501
        """Put Watcher Group  # noqa: E501

        Update watcher group's name or description. Only groups of type `owned_by_me` are allowed to be updated.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_put(group_uid, watcher_groups_group_uid_put_request, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_groups_group_uid_put_request: JSON request body (required)
        :type watcher_groups_group_uid_put_request: WatcherGroupsGroupUidPutRequest
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: SimpleWatcherGroupSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_put_with_http_info(group_uid, watcher_groups_group_uid_put_request, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_put_with_http_info(self, group_uid, watcher_groups_group_uid_put_request, **kwargs):  # noqa: E501
        """Put Watcher Group  # noqa: E501

        Update watcher group's name or description. Only groups of type `owned_by_me` are allowed to be updated.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_put_with_http_info(group_uid, watcher_groups_group_uid_put_request, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_groups_group_uid_put_request: JSON request body (required)
        :type watcher_groups_group_uid_put_request: WatcherGroupsGroupUidPutRequest
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(SimpleWatcherGroupSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'group_uid',
            'watcher_groups_group_uid_put_request'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_put" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_put`")  # noqa: E501
        # verify the required parameter 'watcher_groups_group_uid_put_request' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_groups_group_uid_put_request') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_groups_group_uid_put_request` when calling `watcher_groups_group_uid_put`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        if 'watcher_groups_group_uid_put_request' in local_var_params:
            body_params = local_var_params['watcher_groups_group_uid_put_request']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # HTTP header `Content-Type`
        content_types_list = local_var_params.get('_content_type',
            self.api_client.select_header_content_type(
                ['application/json'],
                'PUT', body_params))  # noqa: E501
        if content_types_list:
                header_params['Content-Type'] = content_types_list

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "SimpleWatcherGroupSchema",
            404: "str",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}', 'PUT',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_watchers_get(self, group_uid, **kwargs):  # noqa: E501
        """Get Watchers list  # noqa: E501

        Returns list of `Watchers` of a given Watcher group.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_get(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: WatcherSchemaResponse
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_watchers_get_with_http_info(group_uid, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_watchers_get_with_http_info(self, group_uid, **kwargs):  # noqa: E501
        """Get Watchers list  # noqa: E501

        Returns list of `Watchers` of a given Watcher group.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_get_with_http_info(group_uid, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(WatcherSchemaResponse, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'group_uid'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_watchers_get" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_watchers_get`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "WatcherSchemaResponse",
            404: "str",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}/watchers', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_watchers_post(self, group_uid, watcher_request_body_post, **kwargs):  # noqa: E501
        """Create Watcher  # noqa: E501

        Create new watcher in a given Watcher group from a json object supplied in request body  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_post(group_uid, watcher_request_body_post, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_request_body_post: JSON request body (required)
        :type watcher_request_body_post: WatcherRequestBodyPost
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: WatcherSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_watchers_post_with_http_info(group_uid, watcher_request_body_post, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_watchers_post_with_http_info(self, group_uid, watcher_request_body_post, **kwargs):  # noqa: E501
        """Create Watcher  # noqa: E501

        Create new watcher in a given Watcher group from a json object supplied in request body  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_post_with_http_info(group_uid, watcher_request_body_post, async_req=True)
        >>> result = thread.get()

        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_request_body_post: JSON request body (required)
        :type watcher_request_body_post: WatcherRequestBodyPost
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(WatcherSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'group_uid',
            'watcher_request_body_post'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_watchers_post" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_watchers_post`")  # noqa: E501
        # verify the required parameter 'watcher_request_body_post' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_request_body_post') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_request_body_post` when calling `watcher_groups_group_uid_watchers_post`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        if 'watcher_request_body_post' in local_var_params:
            body_params = local_var_params['watcher_request_body_post']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # HTTP header `Content-Type`
        content_types_list = local_var_params.get('_content_type',
            self.api_client.select_header_content_type(
                ['application/json'],
                'POST', body_params))  # noqa: E501
        if content_types_list:
                header_params['Content-Type'] = content_types_list

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "WatcherSchema",
            412: "WatcherGroupsGroupUidWatchersPost412Response",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}/watchers', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_watchers_watcher_uid_delete(self, watcher_uid, group_uid, **kwargs):  # noqa: E501
        """Delete Watcher  # noqa: E501

        Delete a given watcher in a given watcher group specified by watcher-uid and group-uid parameters. Confirmed with \"No Content\" response.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_delete(watcher_uid, group_uid, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_watchers_watcher_uid_delete_with_http_info(watcher_uid, group_uid, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_watchers_watcher_uid_delete_with_http_info(self, watcher_uid, group_uid, **kwargs):  # noqa: E501
        """Delete Watcher  # noqa: E501

        Delete a given watcher in a given watcher group specified by watcher-uid and group-uid parameters. Confirmed with \"No Content\" response.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_delete_with_http_info(watcher_uid, group_uid, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: None
        """

        local_var_params = locals()

        all_params = [
            'watcher_uid',
            'group_uid'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_watchers_watcher_uid_delete" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'watcher_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_delete`")  # noqa: E501
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_delete`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'watcher_uid' in local_var_params:
            path_params['watcher-uid'] = local_var_params['watcher_uid']  # noqa: E501
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {}

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}/watchers/{watcher-uid}', 'DELETE',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_watchers_watcher_uid_get(self, watcher_uid, group_uid, **kwargs):  # noqa: E501
        """Get Watcher  # noqa: E501

        Get single Watcher from given Watcher group.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_get(watcher_uid, group_uid, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: WatcherSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_watchers_watcher_uid_get_with_http_info(watcher_uid, group_uid, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_watchers_watcher_uid_get_with_http_info(self, watcher_uid, group_uid, **kwargs):  # noqa: E501
        """Get Watcher  # noqa: E501

        Get single Watcher from given Watcher group.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_get_with_http_info(watcher_uid, group_uid, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(WatcherSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'watcher_uid',
            'group_uid'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_watchers_watcher_uid_get" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'watcher_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_get`")  # noqa: E501
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_get`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'watcher_uid' in local_var_params:
            path_params['watcher-uid'] = local_var_params['watcher_uid']  # noqa: E501
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "WatcherSchema",
            404: "str",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}/watchers/{watcher-uid}', 'GET',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_group_uid_watchers_watcher_uid_put(self, watcher_uid, group_uid, watcher_request_body_put, **kwargs):  # noqa: E501
        """Put Watcher  # noqa: E501

        Editing of existing watcher in a given Watcher group from a json object supplied in request body. Whole watcher body should be supplied (watcher may be muted separately, without specifying the whole watcher body)   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_put(watcher_uid, group_uid, watcher_request_body_put, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_request_body_put: JSON request body (required)
        :type watcher_request_body_put: WatcherRequestBodyPut
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: WatcherSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_group_uid_watchers_watcher_uid_put_with_http_info(watcher_uid, group_uid, watcher_request_body_put, **kwargs)  # noqa: E501

    def watcher_groups_group_uid_watchers_watcher_uid_put_with_http_info(self, watcher_uid, group_uid, watcher_request_body_put, **kwargs):  # noqa: E501
        """Put Watcher  # noqa: E501

        Editing of existing watcher in a given Watcher group from a json object supplied in request body. Whole watcher body should be supplied (watcher may be muted separately, without specifying the whole watcher body)   # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_group_uid_watchers_watcher_uid_put_with_http_info(watcher_uid, group_uid, watcher_request_body_put, async_req=True)
        >>> result = thread.get()

        :param watcher_uid: Unique identifier of watcher. (required)
        :type watcher_uid: str
        :param group_uid: Watcher group identifier. (required)
        :type group_uid: str
        :param watcher_request_body_put: JSON request body (required)
        :type watcher_request_body_put: WatcherRequestBodyPut
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(WatcherSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'watcher_uid',
            'group_uid',
            'watcher_request_body_put'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_group_uid_watchers_watcher_uid_put" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'watcher_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_put`")  # noqa: E501
        # verify the required parameter 'group_uid' is set
        if self.api_client.client_side_validation and local_var_params.get('group_uid') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `group_uid` when calling `watcher_groups_group_uid_watchers_watcher_uid_put`")  # noqa: E501
        # verify the required parameter 'watcher_request_body_put' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_request_body_put') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_request_body_put` when calling `watcher_groups_group_uid_watchers_watcher_uid_put`")  # noqa: E501

        collection_formats = {}

        path_params = {}
        if 'watcher_uid' in local_var_params:
            path_params['watcher-uid'] = local_var_params['watcher_uid']  # noqa: E501
        if 'group_uid' in local_var_params:
            path_params['group-uid'] = local_var_params['group_uid']  # noqa: E501

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        if 'watcher_request_body_put' in local_var_params:
            body_params = local_var_params['watcher_request_body_put']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # HTTP header `Content-Type`
        content_types_list = local_var_params.get('_content_type',
            self.api_client.select_header_content_type(
                ['application/json'],
                'PUT', body_params))  # noqa: E501
        if content_types_list:
                header_params['Content-Type'] = content_types_list

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "WatcherSchema",
            412: "WatcherGroupsGroupUidWatchersPost412Response",
        }

        return self.api_client.call_api(
            '/watcherGroups/{group-uid}/watchers/{watcher-uid}', 'PUT',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))

    def watcher_groups_post(self, watcher_groups_post_request, **kwargs):  # noqa: E501
        """Create Watcher Group  # noqa: E501

        Create watcher group from json object supplied in a request body which contains name and description  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_post(watcher_groups_post_request, async_req=True)
        >>> result = thread.get()

        :param watcher_groups_post_request: JSON request body (required)
        :type watcher_groups_post_request: WatcherGroupsPostRequest
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: SimpleWatcherGroupSchema
        """
        kwargs['_return_http_data_only'] = True
        return self.watcher_groups_post_with_http_info(watcher_groups_post_request, **kwargs)  # noqa: E501

    def watcher_groups_post_with_http_info(self, watcher_groups_post_request, **kwargs):  # noqa: E501
        """Create Watcher Group  # noqa: E501

        Create watcher group from json object supplied in a request body which contains name and description  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.watcher_groups_post_with_http_info(watcher_groups_post_request, async_req=True)
        >>> result = thread.get()

        :param watcher_groups_post_request: JSON request body (required)
        :type watcher_groups_post_request: WatcherGroupsPostRequest
        :param async_req: Whether to execute the request asynchronously.
        :type async_req: bool, optional
        :param _return_http_data_only: response data without head status code
                                       and headers
        :type _return_http_data_only: bool, optional
        :param _preload_content: if False, the urllib3.HTTPResponse object will
                                 be returned without reading/decoding response
                                 data. Default is True.
        :type _preload_content: bool, optional
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the authentication
                              in the spec for a single request.
        :type _request_auth: dict, optional
        :type _content_type: string, optional: force content-type for the request
        :return: Returns the result object.
                 If the method is called asynchronously,
                 returns the request thread.
        :rtype: tuple(SimpleWatcherGroupSchema, status_code(int), headers(HTTPHeaderDict))
        """

        local_var_params = locals()

        all_params = [
            'watcher_groups_post_request'
        ]
        all_params.extend(
            [
                'async_req',
                '_return_http_data_only',
                '_preload_content',
                '_request_timeout',
                '_request_auth',
                '_content_type',
                '_headers'
            ]
        )

        for key, val in six.iteritems(local_var_params['kwargs']):
            if key not in all_params:
                raise ApiTypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method watcher_groups_post" % key
                )
            local_var_params[key] = val
        del local_var_params['kwargs']
        # verify the required parameter 'watcher_groups_post_request' is set
        if self.api_client.client_side_validation and local_var_params.get('watcher_groups_post_request') is None:  # noqa: E501
            raise ApiValueError("Missing the required parameter `watcher_groups_post_request` when calling `watcher_groups_post`")  # noqa: E501

        collection_formats = {}

        path_params = {}

        query_params = []

        header_params = dict(local_var_params.get('_headers', {}))

        form_params = []
        local_var_files = {}

        body_params = None
        if 'watcher_groups_post_request' in local_var_params:
            body_params = local_var_params['watcher_groups_post_request']
        # HTTP header `Accept`
        header_params['Accept'] = self.api_client.select_header_accept(
            ['application/json', 'text/plain'])  # noqa: E501

        # HTTP header `Content-Type`
        content_types_list = local_var_params.get('_content_type',
            self.api_client.select_header_content_type(
                ['application/json'],
                'POST', body_params))  # noqa: E501
        if content_types_list:
                header_params['Content-Type'] = content_types_list

        # Authentication setting
        auth_settings = ['BasicAuth']  # noqa: E501

        response_types_map = {
            200: "SimpleWatcherGroupSchema",
            412: "WatcherGroupsPost412Response",
        }

        return self.api_client.call_api(
            '/watcherGroups', 'POST',
            path_params,
            query_params,
            header_params,
            body=body_params,
            post_params=form_params,
            files=local_var_files,
            response_types_map=response_types_map,
            auth_settings=auth_settings,
            async_req=local_var_params.get('async_req'),
            _return_http_data_only=local_var_params.get('_return_http_data_only'),  # noqa: E501
            _preload_content=local_var_params.get('_preload_content', True),
            _request_timeout=local_var_params.get('_request_timeout'),
            collection_formats=collection_formats,
            _request_auth=local_var_params.get('_request_auth'))
