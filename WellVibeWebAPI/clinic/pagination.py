from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class that allows API endpoints to paginate querysets.

    The client can control the page size by providing a `page_size` query parameter up to a maximum of 100.
    If the client does not provide the `page_size` query parameter, the API will use a default size of 10.
    """

    page_size = 10  # Default number of items to display on each page
    page_size_query_param = "page_size"  # Query parameter name for the client to specify the page size
    max_page_size = 100  # Maximum allowable page size regardless of what the client requests
