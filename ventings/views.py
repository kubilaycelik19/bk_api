from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Venting
from .serializers import VentingSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ventings_view(request):
    if request.method == 'POST':
        serializer = VentingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET -> sadece admin görebilir
    if not request.user.is_staff:
        return Response(
            {'detail': 'Bu kayıtlara sadece admin kullanıcılar erişebilir.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    queryset = (
        Venting.objects.select_related('user')
        .order_by('-created_at')
    )
    serializer = VentingSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

