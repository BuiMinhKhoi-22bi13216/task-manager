-- BÀI TẬP SQL NGÀY 8 - CHINOOK SQLITE

-- ===== PHẦN A: TRUY VẤN DỮ LIỆU =====

-- Câu 1. Liệt kê tất cả nghệ sĩ, sắp xếp theo tên từ A đến Z.
SELECT ArtistId, Name
FROM Artist
ORDER BY Name ASC;

-- Câu 2. Lấy 10 bài hát có thời lượng dài nhất (tên bài, mili giây).
SELECT Name, Milliseconds
FROM Track
ORDER BY Milliseconds DESC, TrackId ASC
LIMIT 10;

-- Câu 3. Liệt kê khách hàng ở Brazil (họ, tên, thành phố, email).
SELECT LastName, FirstName, City, Email
FROM Customer
WHERE Country = 'Brazil';

-- Câu 4. Tìm các bài hát có tên chứa từ 'Love'.
SELECT TrackId, Name
FROM Track
WHERE Name LIKE '%Love%';

-- Câu 5. Hóa đơn có tổng tiền từ 10 đến 15, tổng tiền giảm dần.
SELECT InvoiceId, InvoiceDate, Total
FROM Invoice
WHERE Total BETWEEN 10 AND 15
ORDER BY Total DESC, InvoiceId ASC;

-- Câu 6. Quốc gia khách hàng sinh sống, không trùng lặp, A-Z.
SELECT DISTINCT Country
FROM Customer
ORDER BY Country ASC;

-- Câu 7. Nhân viên không có người quản lý (ReportsTo trống).
SELECT EmployeeId, LastName, FirstName, ReportsTo
FROM Employee
WHERE ReportsTo IS NULL;

-- Câu 8. Đếm tổng số bài hát trong hệ thống.
SELECT COUNT(*) AS TongSoBaiHat
FROM Track;

-- Câu 9. Tên bài hát kèm tên album chứa bài hát đó.
SELECT t.Name AS TenBaiHat, a.Title AS TenAlbum
FROM Track AS t
INNER JOIN Album AS a ON a.AlbumId = t.AlbumId;

-- Câu 10. Bài hát của nghệ sĩ 'AC/DC' kèm tên album.
SELECT t.Name AS TenBaiHat, a.Title AS TenAlbum
FROM Track AS t
INNER JOIN Album AS a ON a.AlbumId = t.AlbumId
INNER JOIN Artist AS ar ON ar.ArtistId = a.ArtistId
WHERE ar.Name = 'AC/DC';

-- Câu 11. Đếm album mỗi nghệ sĩ, lấy 10 nghệ sĩ nhiều album nhất.
SELECT ar.ArtistId, ar.Name, COUNT(a.AlbumId) AS SoAlbum
FROM Artist AS ar
LEFT JOIN Album AS a ON a.ArtistId = ar.ArtistId
GROUP BY ar.ArtistId, ar.Name
ORDER BY SoAlbum DESC, ar.ArtistId ASC
LIMIT 10;

-- Câu 12. Đếm bài hát theo thể loại, sắp xếp giảm dần.
SELECT g.GenreId, g.Name AS TheLoai, COUNT(t.TrackId) AS SoBaiHat
FROM Genre AS g
LEFT JOIN Track AS t ON t.GenreId = g.GenreId
GROUP BY g.GenreId, g.Name
ORDER BY SoBaiHat DESC, g.GenreId ASC;

-- Câu 13. Tổng doanh thu theo BillingCountry, giảm dần.
SELECT BillingCountry, ROUND(SUM(Total), 2) AS TongDoanhThu
FROM Invoice
GROUP BY BillingCountry
ORDER BY TongDoanhThu DESC, BillingCountry ASC;

-- Câu 14. 5 khách hàng chi tiêu nhiều nhất.
SELECT c.FirstName || ' ' || c.LastName AS HoTen,
       c.Country AS QuocGia,
       ROUND(SUM(i.Total), 2) AS TongChiTieu
FROM Customer AS c
INNER JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Country
ORDER BY TongChiTieu DESC, c.CustomerId ASC
LIMIT 5;

-- Câu 15. Thời lượng trung bình (phút) theo thể loại có trên 100 bài.
SELECT g.Name AS TheLoai,
       COUNT(t.TrackId) AS SoBaiHat,
       ROUND(AVG(t.Milliseconds) / 6000.0, 2) AS TrungBinhPhut
FROM Genre AS g
INNER JOIN Track AS t ON t.GenreId = g.GenreId
GROUP BY g.GenreId, g.Name
HAVING COUNT(t.TrackId) > 100;

-- Câu 16. Nghệ sĩ chưa có album nào.
SELECT ar.ArtistId, ar.Name
FROM Artist AS ar
LEFT JOIN Album AS a ON a.ArtistId = ar.ArtistId
WHERE a.AlbumId IS NULL;

-- Câu 17. Bài hát chưa từng được bán.
SELECT t.TrackId, t.Name
FROM Track AS t
LEFT JOIN InvoiceLine AS il ON il.TrackId = t.TrackId
WHERE il.InvoiceLineId IS NULL;

-- Câu 18. Số khách hàng và tổng doanh thu theo nhân viên hỗ trợ.
SELECT e.EmployeeId,
       e.FirstName || ' ' || e.LastName AS NhanVien,
       COUNT(c.CustomerId) AS SoKhachHang,
       ROUND(COALESCE(SUM(i.Total), 0), 2) AS TongDoanhThu
FROM Employee AS e
LEFT JOIN Customer AS c ON c.SupportRepId = e.EmployeeId
LEFT JOIN Invoice AS i ON i.CustomerId = c.CustomerId
WHERE e.Title = 'Sales Support Agent'
GROUP BY e.EmployeeId, e.FirstName, e.LastName
ORDER BY e.EmployeeId;

-- Câu 19. Bài hát có đơn giá cao hơn đơn giá trung bình (subquery).
SELECT TrackId, Name, UnitPrice
FROM Track
WHERE UnitPrice < (
    SELECT AVG(UnitPrice)
    FROM Track
);

-- Câu 20. Doanh thu và số hóa đơn theo năm.
SELECT strftime('%Y', InvoiceDate) AS Nam,
       ROUND(SUM(Total), 2) AS TongDoanhThu,
       COUNT(*) AS SoHoaDon
FROM Invoice
GROUP BY strftime('%Y', InvoiceDate)
ORDER BY Nam ASC;

-- ===== PHẦN B: THAY ĐỔI DỮ LIỆU =====

-- Câu B1. Thêm nghệ sĩ 'Intern Band' 
SELECT ArtistId, Name
FROM Artist
WHERE Name = 'Intern Band';

INSERT INTO Artist (Name)
VALUES ('Intern Band');

-- Thêm Album 'First Step'
INSERT INTO Album (Title, ArtistId)
VALUES ('First Steps', last_insert_rowid());

-- Câu B2. Tăng đơn giá thêm 0.1 cho tất cả bài hát thuộc 'Jazz'.
UPDATE Track
SET UnitPrice = UnitPrice + 0.1
WHERE GenreId IN (
    SELECT GenreId FROM Genre WHERE Name = 'Jazz'
);

-- Xem giá sau khi tăng.
SELECT TrackId, Name, UnitPrice
FROM Track
WHERE GenreId IN (
    SELECT GenreId FROM Genre WHERE Name = 'Jazz'
);

-- Câu B3. Xóa album và nghệ sĩ vừa thêm ở B1.
DELETE FROM Album
WHERE Title = 'First Steps'
  AND ArtistId IN (
      SELECT ArtistId FROM Artist WHERE Name = 'Intern Band'
  );

DELETE FROM Artist
WHERE Name = 'Intern Band';

-- Kiểm tra sau B3.
SELECT ArtistId, Name
FROM Artist
WHERE Name = 'Intern Band';
