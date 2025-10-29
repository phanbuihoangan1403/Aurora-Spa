from django.shortcuts import render
def admin_faq(request):
    return render (request,'admin_faq.html')
def admin_tichdiem(request):
    return render (request, 'admin_tichdiem.html')
def khachhang_faq(request):
    return render (request,'khachhang_faq.html')
def khachhang_tichdiem(request):
    return render (request,'khachhang_tichdiem.html')
# Create your views here.
