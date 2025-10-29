from django.db import models
from django.db.models import F
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator, EmailValidator
from django.contrib.auth.hashers import make_password, check_password



class QuyDoiDiem(models.Model):
    MaQuyDoi = models.CharField(
        primary_key=True,   # thêm khóa chính
        max_length=5,
        help_text='Mã quy đổi'
    )
    GiaTriDiem = models.IntegerField(
        help_text='Giá trị điểm (số điểm cần để quy đổi)'
    )
    GiaTriQuyDoi = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Giá trị quy đổi tương ứng (VNĐ)'
    )

    class Meta:
        db_table = 'QuyDoiDiem'
        verbose_name = 'Quy Đổi Điểm'
        verbose_name_plural = 'Quy Đổi Điểm'

    def __str__(self):
        return f"{self.MaQuyDoi} - {self.GiaTriDiem} điểm = {self.GiaTriQuyDoi} VNĐ"


class LichSuTichDiem(models.Model):
    MaGiaoDich = models.CharField(
        primary_key=True,   # thêm khóa chính
        max_length=5,
        help_text='Mã giao dịch'
    )

    LOAIGIAODICH_CHOICES = [
        ('Tích điểm', 'Tích điểm'),
        ('Quy đổi điểm', 'Quy đổi điểm'),
    ]

    LoaiGiaoDich = models.CharField(
        choices=LOAIGIAODICH_CHOICES,
        max_length=50,
        help_text='Loại giao dịch'
    )
    ChiTietGiaoDich = models.CharField(
        max_length=300,
        help_text='Chi tiết giao dịch'
    )
    NgayGiaoDich = models.DateTimeField(
        auto_now_add=True,
        help_text='Ngày giao dịch'
    )
    MaQuyDoi = models.ForeignKey(
        QuyDoiDiem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Chính sách quy đổi được áp dụng (nếu có)"
    )
    MaKhachHang = models.ForeignKey(
        "KhachHang",  # giữ dạng chuỗi để tránh lỗi import
        on_delete=models.CASCADE,
        help_text="Khách hàng thực hiện giao dịch"
    )
    SoDiemThayDoi = models.IntegerField(
        help_text="Số điểm thay đổi (+ hoặc -)"
    )

    def save(self, *args, **kwargs):
        from .models import DiemTichLuy  # import cục bộ để tránh vòng lặp

        # Lấy ví điểm hiện tại
        diem_tl = DiemTichLuy.objects.get(MaKhachHang=self.MaKhachHang)

        # Kiểm tra không cho trừ quá số điểm hiện có
        if self.SoDiemThayDoi < 0 and diem_tl.SoDiemHienTai + self.SoDiemThayDoi < 0:
            raise ValidationError("Không thể trừ quá số điểm hiện có!")

        # Lưu bản ghi giao dịch
        super().save(*args, **kwargs)

        # Cập nhật tổng điểm trong DiemTichLuy
        DiemTichLuy.objects.filter(MaKhachHang=self.MaKhachHang).update(
            SoDiemHienTai=F('SoDiemHienTai') + self.SoDiemThayDoi
        )

    class Meta:
        db_table = 'LichSuTichDiem'
        verbose_name = 'Lịch Sử Tích Điểm'
        verbose_name_plural = 'Lịch Sử Tích Điểm'

    def __str__(self):
        sign = "+" if self.SoDiemThayDoi >= 0 else ""
        return f"{self.MaGiaoDich} ({sign}{self.SoDiemThayDoi} điểm)"


# Mỗi khách hàng đăng ký tài khoản đều có điểm tích lũy (tự động tạo khi KhachHang được tạo)
@receiver(post_save, sender="aurora.KhachHang")  # thay 'your_app_name' = tên app thật
def tao_diem_tich_luy(sender, instance, created, **kwargs):
    from .models import DiemTichLuy
    if created:
        DiemTichLuy.objects.create(MaKhachHang=instance, SoDiemHienTai=0)


class FAQ (models.Model):
    MaCauHoi = models.CharField(
        max_length=5,
        primary_key=True,
        help_text='Mã câu hỏi'
    )
    MaNhanVien=models. ForeignKey('NhanVien', on_delete=models.CASCADE, help_text='Mã nhân viên')
    CauHoi=models.CharField(
        max_length=300,
        help_text='Cau Hoi'
    )
    CauTraLoi=models.TextField(
        help_text='Câu trả lời'
    )
    NgayCapNhat=models.DateTimeField(
        auto_now_add=True,
        help_text='Ngày cập nhật gần nhất'
    )
    TrangThaiHienThi=models.BooleanField(default=True, help_text="Trạng thái hiển thị")

    class Meta:
        db_table = 'FAQ'
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
    def __str__(self):
        return self.MaCauHoi


# MODEL: KHÁCH HÀNG
class KhachHang(models.Model):
    MaKhachHang = models.CharField(
        max_length=5,
        primary_key=True,
        validators=[MinLengthValidator(5)],
        help_text="Mã khách hàng (VD: KH001, KH002,...)"
    )

    HoVaTen = models.CharField(
        max_length=100,
        help_text="Tên khách hàng"
    )

    Email = models.CharField(
        max_length=100,
        unique=True,
        validators=[EmailValidator(message="Email không hợp lệ")],
        help_text="Email đăng ký"
    )

    SDT = models.CharField(
        max_length=10,
        validators=[MinLengthValidator(10)],
        help_text="Số điện thoại"
    )

    MatKhau = models.CharField(
        max_length=255,
        help_text="Mật khẩu đã mã hóa"
    )

    class Meta:
        db_table = 'KhachHang'
        verbose_name = 'Khách Hàng'
        verbose_name_plural = 'Khách Hàng'

    def set_password(self, raw_password):
        """Mã hóa mật khẩu"""
        self.MatKhau = make_password(raw_password)

    def check_password(self, raw_password):
        """Kiểm tra mật khẩu"""
        return check_password(raw_password, self.MatKhau)

    def __str__(self):
        return f"{self.MaKhachHang} - {self.HoVaTen}"

# MODEL: LỊCH HẸN
class LichHen(models.Model):
    # Trạng thái hợp lệ
    TRANG_THAI_CHOICES = [
        ('Đang chờ', 'Đang chờ'),
        ('Đang thực hiện', 'Đang thực hiện'),
        ('Hoàn thành', 'Hoàn thành'),
        ('Đã hủy', 'Đã hủy'),
    ]

    MaLichHen = models.CharField(
        max_length=5,
        primary_key=True,
        validators=[MinLengthValidator(5)],
        help_text="Mã định danh duy nhất cho từng lịch hẹn (LH001, LH002,...)"
    )

    MaKhachHang = models.ForeignKey(
        KhachHang,
        on_delete=models.CASCADE,
        db_column='MaKhachHang',
        help_text="Mã duy nhất đại diện cho mỗi khách hàng"
    )

    MaNhanVien = models.ForeignKey(
        'NhanVien', on_delete=models.CASCADE, db_column='MaNhanVien'
    )
    MaDichVu = models.ForeignKey(
        'DichVu', on_delete=models.CASCADE, db_column='MaDichVu'
    )

    NgayDatLich = models.DateTimeField(
        help_text="Ngày và giờ khách thực hiện đặt lịch"
    )

    NgayHen = models.DateTimeField(
        help_text="Ngày và giờ hẹn thực tế để thực hiện dịch vụ"
    )

    TrangThai = models.CharField(
        max_length=25,
        choices=TRANG_THAI_CHOICES,
        help_text="Mô tả trạng thái hiện tại của lịch hẹn"
    )

    class Meta:
        db_table = 'LichHen'
        verbose_name = 'Lịch Hẹn'
        verbose_name_plural = 'Lịch Hẹn'
        constraints = [
            models.CheckConstraint(
                check=models.Q(TrangThai__in=[
                    'Đang chờ', 'Đang thực hiện', 'Hoàn thành', 'Đã hủy'
                ]),
                name='chk_trangthai_lichhen'
            )
        ]

    def __str__(self):
        return f"{self.MaLichHen} - {self.MaKhachHang.HoVaTen} - {self.NgayHen.strftime('%d/%m/%Y %H:%M')} - {self.TrangThai}"


# MODEL: DANH MỤC DỊCH VỤ
class DanhMucDichVu(models.Model):
    MaDanhMuc = models.CharField(
        max_length=5,
        primary_key=True,
        validators=[MinLengthValidator(5)],
        help_text="Mã định danh duy nhất cho từng danh mục dịch vụ Spa (VD: DM001, DM002, ...)"
    )

    TenDanhMuc = models.CharField(
        max_length=200,
        null=False,
        help_text="Tên danh mục dịch vụ (VD: 'Chăm sóc da mặt', 'Massage thư giãn')"
    )

    MoTa = models.TextField(
        null=True,
        blank=True,
        help_text="Mô tả chi tiết về nhóm dịch vụ (VD: các loại liệu trình trong danh mục)"
    )

    class Meta:
        db_table = 'DanhMucDichVu'
        verbose_name = 'Danh Mục Dịch Vụ'
        verbose_name_plural = 'Danh Mục Dịch Vụ'

    def __str__(self):
        return f"{self.MaDanhMuc} - {self.TenDanhMuc}"


# MODEL: DỊCH VỤ
class DichVu(models.Model):
    MaDichVu = models.CharField(
        max_length=5,
        primary_key=True,
        validators=[MinLengthValidator(5)],
        help_text="Mã định danh duy nhất cho từng dịch vụ (VD: DV001, DV002, ...)"
    )

    MaDanhMuc = models.ForeignKey(
        DanhMucDichVu,
        on_delete=models.CASCADE,
        db_column='MaDanhMuc',
        help_text="Khóa ngoại liên kết đến bảng DanhMucDichVu (MaDanhMuc)"
    )

    TenDichVu = models.CharField(
        max_length=200,
        null=False,
        help_text="Tên dịch vụ Spa (VD: 'Massage đá nóng', 'Trị mụn chuyên sâu')"
    )

    MoTa = models.TextField(
        null=False,
        help_text="Mô tả nội dung, liệu trình, sản phẩm sử dụng, giá và thời gian dịch vụ"
    )

    TrangThaiHienThi = models.BooleanField(
        default=True,
        help_text="Trạng thái hiển thị dịch vụ (1 = đang kinh doanh, 0 = tạm ẩn)"
    )

    class Meta:
        db_table = 'DichVu'
        verbose_name = 'Dịch Vụ'
        verbose_name_plural = 'Dịch Vụ'

    def __str__(self):
        return f"{self.MaDichVu} - {self.TenDichVu}"

# MODEL: ĐIỂM TÍCH LŨY
class DiemTichLuy(models.Model):
    MaKhachHang = models.OneToOneField(
        'KhachHang',                      # Khóa ngoại liên kết đến bảng KhachHang
        on_delete=models.CASCADE,
        db_column='MaKhachHang',
        primary_key=True,                 # Vừa là khóa chính, vừa là khóa ngoại
        validators=[MinLengthValidator(5)],
        help_text="Mã khách hàng (VD: KH001, KH002, ...)"
    )

    SoDiemHienTai = models.IntegerField(
        default=0,
        help_text="Số điểm tích lũy hiện tại của khách hàng"
    )

    class Meta:
        db_table = 'DiemTichLuy'
        verbose_name = 'Điểm Tích Lũy'
        verbose_name_plural = 'Điểm Tích Lũy'

    def __str__(self):
        return f"{self.MaKhachHang.MaKhachHang} - {self.MaKhachHang.HoVaTen} ({self.SoDiemHienTai} điểm)"


class NhanVien(models.Model):
    VAI_TRO_CHOICES = [
        ('Admin', 'Admin'),
        ('Chăm sóc khách hàng', 'Chăm sóc khách hàng'),
        ('Chuyên viên spa', 'Chuyên viên spa'),
    ]

    MaNhanVien = models.CharField(max_length=5, primary_key=True, unique=True)
    HoVaTen = models.CharField(max_length=100)
    Email = models.EmailField(max_length=100, unique=True)
    SDT = models.CharField(max_length=10, unique=True)
    MatKhau = models.CharField(max_length=255)
    VaiTro = models.CharField(max_length=30, choices=VAI_TRO_CHOICES)
    TrangThai = models.BooleanField(default=True)

    class Meta:
        db_table = 'NhanVien'
        verbose_name = 'Nhân Viên'
        verbose_name_plural = 'Nhân viên'

    def __str__(self):
        return f"{self.HoVaTen} ({self.VaiTro})"


class Blog(models.Model):
    MaBaiViet = models.CharField(max_length=5, primary_key=True)
    MaNhanVien = models.ForeignKey(
        'NhanVien',
        on_delete=models.CASCADE,
        db_column='MaNhanVien',
        help_text='Nhân viên đăng bài viết'
    )
    TieuDeBaiViet = models.CharField(max_length=200)
    NoiDungBaiViet = models.TextField()
    NgayDang = models.DateTimeField()
    TrangThaiHienThi = models.BooleanField(default=True)

    class Meta:
        db_table = 'Blog'
        verbose_name = 'Blog'
        verbose_name_plural = 'Blog'

    def __str__(self):
        return self.TieuDeBaiViet
