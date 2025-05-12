from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.exceptions import APIException

from django.db import transaction


from . import Message, QueryParams, Export


class SmartAPIView(APIView):
    role_permission = False
    query_params = QueryParams

    def not_found(self, text="Object not found"):

        return Response(Message.create(text), status=status.HTTP_404_NOT_FOUND)

    def respond_with(self, text, key="detail", status_code=status.HTTP_200_OK):

        return Response(Message.create(text, key), status=status_code)

    def get_user_from_request(self):
        return self.request.user

    def is_anonymous_request(self):
        return self.request.user.is_anonymous

    def is_role_permission(self):
        return self.role_permission

    def get_role_permission(self, model):

        role_permissions = self.get_permissions()

        if not role_permissions:
            return None

        key = None

        if hasattr(model, "get_permission_key"):
            key = model.get_permission_key(self)

        if role_permissions is None or key is None:
            return None

        permissions = getattr(role_permissions, key)

        return permissions

    def has_role_permission(self, method, model):
        permissions = self.get_role_permission(model)

        if permissions is None:
            return True

        if method == "GET" and "view_owned" not in permissions and "view_all" not in permissions:
            return False

        if method in ["POST", "PUT"] and "create" not in permissions:
            return False

        if method == "PATCH" and "edit_owned" not in permissions and "edit_all" not in permissions:
            return False

        if method == "DELETE" and "delete_owned" not in permissions and "delete_all" not in permissions:
            return False

        return True

    def get_permissions(self):
        return []

    def get_permission_denied_response(self, request, action):
        return self.respond_with("You do not have permission to access this",
                                 status_code=status.HTTP_403_FORBIDDEN)


class SmartDetailAPIView(SmartAPIView):

    model = None
    edit_serializer = None
    detail_serializer = None
    deletable = False
    partial = True

    role_permission = False

    def queryset(self, request, id):
        objects = QueryParams.get_str(request, "objects")

        if objects == "all":
            return self.model.all_objects.filter(id=id)
        elif objects == "deleted":
            return self.model.all_objects.filter(id=id, deleted_at__isnull=False)

        return self.model.objects.filter(id=id)

    def get(self, request, id):

        if not self.has_permission(request, "GET") or not self.has_role_permission("GET", self.model):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request, id)

        queryset = self.filter_queryset(queryset, "GET")

        queryset = self.add_filters(queryset, request)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "GET")

        if not self.get_detail_serializer(request, instance):
            return self.get_missing_serializer_response(request, "GET")

        return self.handle_get(request, instance)

    @transaction.atomic
    def patch(self, request, id):

        if not self.has_permission(request, "PATCH") or not self.has_role_permission("PATCH", self.model):
            return self.get_permission_denied_response(request, "PATCH")

        queryset = self.queryset(request, id)

        queryset = self.filter_queryset(queryset, "PATCH")

        queryset = self.add_filters(queryset, request)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "GET")

        if not self.get_edit_serializer(request, instance):
            return self.get_missing_serializer_response(request, "PATCH")

        data = self.override_patch_data(request, request.data)

        edit_serializer_class = self.get_edit_serializer(request, instance)
        edit_serializer = edit_serializer_class(data=data, partial=self.partial, instance=instance)
        edit_serializer.is_valid(raise_exception=True)
        instance = edit_serializer.update(instance, edit_serializer.validated_data)

        detail_serializer_class = self.get_detail_serializer(request, instance)
        data = detail_serializer_class(instance).data

        return Response(data, status=status.HTTP_200_OK)

    @transaction.atomic
    def delete(self, request, id):

        if not self.deletable or not self.has_permission(request, "DELETE") or not self.has_role_permission("DELETE", self.model):
            return self.get_permission_denied_response(request, "DELETE")

        queryset = self.queryset(request, id)

        queryset = self.filter_queryset(queryset, "DELETE")

        queryset = self.add_filters(queryset, request)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "DELETE")

        handle_delete = self.handle_delete(instance)
        if isinstance(handle_delete, Response):
            return handle_delete

        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_role_permission(self):
        return self.role_permission

    def get_edit_serializer(self, request, instance):
        return self.edit_serializer

    def get_detail_serializer(self, request, instance):
        return self.detail_serializer

    def get_instance_not_found_response(self, request, action):
        return self.respond_with("An object with this id does not exist",
                                 status_code=status.HTTP_404_NOT_FOUND)

    def get_missing_serializer_response(self, request, action):
        message = None
        serializer_type = ""
        if action == "GET":
            serializer_type = "Detail serializer"
        elif action == "PATCH":
            serializer_type = "Edit serializer"

        message = f"{serializer_type} is not defined"
        return self.respond_with(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_get(self, request, instance):

        detail_serializer_class = self.get_detail_serializer(request, instance)
        data = detail_serializer_class(instance).data

        data = self.override_response_data(request, data)

        return Response(data, status=status.HTTP_200_OK)

    def handle_delete(self, instance):
        return instance.delete()

    def add_filters(self, queryset, request):
        return queryset

    def filter_queryset(self, queryset, method):
        return _filter_queryset(self, queryset, method)

    def has_permission(self, request, method):
        return True

    def override_patch_data(self, request, data):
        return data

    def override_response_data(self, request, data):
        return data

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.detail_serializer

        if self.request.method == 'PATCH':
            return self.edit_serializer

        return self.detail_serializer


# Pagination Classes
class PageBasedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class CursorSetPagination(CursorPagination):
    page_size = 20
    ordering = ('-created_at')


class CursorOrderSetPagination(CursorPagination):
    page_size = 20
    ordering = ('order')


class PaginationAPIView(SmartAPIView):
    max_page_size = 40
    min_page_size = 5
    default_page_size = 20

    pagination_class = CursorSetPagination

    allow_disable_pagination = False

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """

        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                pagination_type = QueryParams.get_str(self.request, "pagination_type")

                if pagination_type == "page":
                    self._paginator = PageBasedPagination()
                else:
                    self._paginator = self.pagination_class()

                # todo cursor pagination ordering doesn't support nesting e.g. order_by 'user__id' will cause crash
                order_by = QueryParams.get_str(self.request, "order_by")
                if order_by and "__" not in order_by:
                    self._paginator.ordering = [order_by]

        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            raise APIException()

        self.set_page_size()

        order_by = QueryParams.get_str(self.request, "order_by")

        if order_by:
            queryset = queryset.order_by(order_by)

        if hasattr(self.paginator, "ordering"):
            if isinstance(self.paginator.ordering, list):
                queryset = queryset.order_by(*self.paginator.ordering)

            elif self.paginator.ordering:
                queryset = queryset.order_by(self.paginator.ordering)


        page = self.paginator.paginate_queryset(queryset, self.request, view=self)
        return page

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def get_response(self, data):
        return Response(data)

    def set_page_size(self, extra=None):

        page_size = self.request.GET.get('page_size')

        if not page_size:
            return

        size = int(page_size)

        if size < self.min_page_size:
            size = self.min_page_size

        if size > self.max_page_size:
            size = self.max_page_size

        self.paginator.page_size = size

    def paginated_response(self, queryset, serializer_class):

        if hasattr(serializer_class, "optimise"):
            queryset = serializer_class.optimise(queryset)
        else:
            print(f"\033[93m{serializer_class} query not optimised\x1b[0m")
            pass

        if QueryParams.get_str(self.request, 'export'):
            return Export.queryset(queryset, self.request)

        order_by = QueryParams.get_str(self.request, "order_by")

        if order_by:
            try:
                queryset = queryset.order_by(order_by)
            except Exception as e:
                return self.respond_with(f"This field: '{order_by}' is not valid", status_code=status.HTTP_400_BAD_REQUEST)

        if self.allow_disable_pagination and QueryParams.get_bool(self.request, 'paginated') is False:
            if not order_by:
                if isinstance(self.paginator.ordering, list):
                    queryset = queryset.order_by(*self.paginator.ordering)
                else:
                    queryset = queryset.order_by(self.paginator.ordering)

            data = serializer_class(queryset, many=True).data
            return self.get_response(data)

        page = self.paginate_queryset(queryset)

        serializer = serializer_class(page, many=True)

        return self.get_paginated_response(serializer.data)


class SmartPaginationAPIView(PaginationAPIView):
    model = None
    create_serializer = None
    detail_serializer = None
    list_serializer = None
    bulk_serializer = None
    bulk_detail_serializer = None

    role_permission = False

    def queryset(self, request):
        objects = QueryParams.get_str(request, "objects")

        if objects == "all":
            return self.model.all_objects.filter()
        elif objects == "deleted":
            return self.model.all_objects.filter(deleted_at__isnull=False)

        return self.model.objects.filter()

    def get(self, request):

        if not self.has_permission(request, "GET") or not self.has_role_permission("GET", self.model):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request)

        queryset = self.filter_queryset(queryset, "GET")

        queryset = self.add_filters(queryset, request)

        if not self.get_list_serializer(request, queryset):
            return self.get_missing_serializer_response(request, "GET")

        serializer_class = self.get_list_serializer(request, queryset)

        return self.paginated_response(queryset, serializer_class)

    @transaction.atomic
    def post(self, request):

        if not self.has_permission(request, "POST") or not self.has_role_permission("POST", self.model):
            return self.get_permission_denied_response(request, "POST")

        if not self.get_create_serializer(request):
            return self.get_missing_serializer_response(request, "POST")

        create_serializer_class = self.get_create_serializer(request)

        data = request.data

        if hasattr(self.request.data, "_mutable"):
            self.request.data._mutable = True

        data = self.override_post_data(request, data)

        if hasattr(self.request.data, "_mutable"):
            self.request.data._mutable = False

        create_serializer = create_serializer_class(data=data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()

        detail_serializer_class = self.get_detail_serializer(request, instance)
        data = detail_serializer_class(instance).data

        return self.post_response(request, instance, data)

    @transaction.atomic
    def put(self, request):

        if not self.has_permission(request, "PUT") or not self.has_role_permission("PUT", self.model):
            return self.get_permission_denied_response(request, "PUT")

        if not self.get_bulk_create_serializer(request):
            return self.get_missing_serializer_response(request, "PUT")

        bulk_create_serializer_class = self.get_bulk_create_serializer(request)

        data = request.data

        if hasattr(self.request.data, "_mutable"):
            self.request.data._mutable = True

        data = self.override_put_data(request, data)

        if hasattr(self.request.data, "_mutable"):
            self.request.data._mutable = False

        bulk_create_serializer = bulk_create_serializer_class(data=data)
        bulk_create_serializer.is_valid(raise_exception=True)
        instance = bulk_create_serializer.save()

        return self.bulk_response(request, instance)

    def is_role_permission(self):
        return self.role_permission

    def post_response(self, request, instance, data):
        return Response(data, status=status.HTTP_201_CREATED)

    def bulk_response(self, request, instance):
        bulk_detail_serializer_class = self.get_bulk_detail_serializer(request, instance)
        data = bulk_detail_serializer_class(instance).data

        return self.post_response(request, instance, data)

    def get_create_serializer(self, request):
        return self.create_serializer

    def get_bulk_create_serializer(self, request):
        return self.bulk_serializer

    def get_list_serializer(self, request, queryset):
        return self.list_serializer

    def get_detail_serializer(self, request, instance):
        return self.detail_serializer

    def get_bulk_detail_serializer(self, request, instance):
        return self.bulk_detail_serializer

    def get_permission_denied_response(self, request, action):
        return self.respond_with("You do not have permission to access this",
                                 status_code=status.HTTP_403_FORBIDDEN)

    def get_missing_serializer_response(self, request, action):
        message = None
        serializer_type = ""
        if action == "GET":
            serializer_type = "List serializer"
        elif action == "POST":
            serializer_type = "Create serializer"

        message = f"{serializer_type} is not defined"
        return self.respond_with(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_filters(self, queryset, request):
        return queryset

    def filter_queryset(self, queryset, method):
        return _filter_queryset(self, queryset, method)

    def has_permission(self, request, method):
        return True

    def override_post_data(self, request, data):
        return data

    def override_put_data(self, request, data):
        return data

    def get_queryset(self):
        return self.queryset(self.request)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return self.list_serializer or self.detail_serializer

        if self.request.method == 'POST':
            return self.create_serializer

        if self.request.method == "PUT":
            return self.bulk_serializer

        return self.list_serializer


def _filter_queryset(view, queryset, method):
    permissions = view.get_role_permission(view.model)
    if permissions is None:
        return queryset

    if method == "GET" and "view_all" in permissions:
        return queryset

    if method == "PATCH" and "edit_all" in permissions:
        return queryset

    if method == "DELETE" and "delete_all" in permissions:
        return queryset

    admin = view.get_admin_from_request()
    return view.model.filter_to_owned(view.model, queryset, admin)

