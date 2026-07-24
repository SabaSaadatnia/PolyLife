from rest_framework import filters, generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from store.models import Product

from .models import Supplement
from .serializers import (
    SupplementDetailSerializer,
    SupplementListSerializer,
)

from rest_framework.views import APIView
from config.permissions import IsTeam4Admin


class SupplementListView(generics.ListAPIView):
    serializer_class = SupplementListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "scientific_name", "description"]

    def get_queryset(self):
        return Supplement.objects.filter(
            is_deleted=False,
        ).order_by("name")


class SupplementDetailView(generics.RetrieveAPIView):
    serializer_class = SupplementDetailSerializer

    def get_queryset(self):
        return Supplement.objects.filter(is_deleted=False)


@api_view(["GET"])
def supplement_store_link(request, pk):
    try:
        supplement = Supplement.objects.get(
            pk=pk,
            is_deleted=False,
        )
    except Supplement.DoesNotExist:
        return Response(
            {"error": "Supplement not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    products = Product.objects.filter(
        supplement_id=pk,
        is_active=True,
        is_deleted=False,
    ).values(
        "id",
        "name",
        "price",
        "stock_quantity",
    )

    store_path = f"/api/store/products/?supplement_id={pk}"

    return Response(
        {
            "supplement_id": supplement.id,
            "supplement_name": supplement.name,
            "store_products": list(products),
            "store_url": request.build_absolute_uri(store_path),
        }
    )

class AdminSupplementListCreateView(APIView):

    permission_classes = [IsTeam4Admin]


    def get(self, request):

        supplements = Supplement.objects.filter(
            is_deleted=False
        )


        serializer = SupplementDetailSerializer(
            supplements,
            many=True
        )

        return Response(serializer.data)



    def post(self, request):

        serializer = SupplementDetailSerializer(
            data=request.data
        )


        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data,
                status=201
            )


        return Response(
            serializer.errors,
            status=400
        )




class AdminSupplementDetailView(APIView):

    permission_classes = [IsTeam4Admin]


    def get_object(self, pk):

        return Supplement.objects.filter(
            id=pk
        ).first()



    def put(self, request, pk):

        supplement = self.get_object(pk)


        if not supplement:

            return Response(
                {"error":"Supplement not found"},
                status=404
            )


        serializer = SupplementDetailSerializer(
            supplement,
            data=request.data,
            partial=True
        )


        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )


        return Response(
            serializer.errors,
            status=400
        )




    def delete(self, request, pk):

        supplement = self.get_object(pk)


        if not supplement:

            return Response(
                {"error":"Supplement not found"},
                status=404
            )


        supplement.is_deleted=True
        supplement.save()


        return Response(
            {
                "message":
                "Supplement deleted"
            }
        )