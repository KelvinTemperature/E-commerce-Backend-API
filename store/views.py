from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdminOrReadOnly
from .models import Product
from .serializers import ProductSerializer


class ProductList(APIView):
    """
    GET  /api/products/   → List all products (authenticated user)
    POST /api/products/   → Create a new product (admin only)
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        products = Product.objects.all().order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetail(APIView):
    """
    GET    /api/products/<id>/  → Get a single product (any authenticated user)
    PUT    /api/products/<id>/  → Update a product (admin only)
    DELETE /api/products/<id>/  → Delete a product (admin only)
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, pk):
        """
        Helper method — reused by get(), put(), delete()
        to avoid repeating the same try/except block.
        """
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = self.get_object(pk)
        if product is None:
            return Response(
                {'error': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        product.delete()
        return Response(
            {'message': 'Product deleted successfully.'},
            status=status.HTTP_200_OK
        )