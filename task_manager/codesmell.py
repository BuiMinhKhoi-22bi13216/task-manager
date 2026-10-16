
import datetime

# Các hằng số
TAX_RATE = 0.08
SHIPPING_STANDARD = 1
SHIPPING_EXPRESS = 2
ORDER_FILE = "orders.txt"

FREE_SHIPPING_FROM = 500_000
SHIPPING_TYPE_1_FEE = 30_000
SHIPPING_TYPE_2_FEE_LOW = 50_000
SHIPPING_TYPE_2_FEE_HIGH = 20_000

DEFAULT_ORDER_DATE = datetime.date(2026, 10, 1)

# Chính sách từng loại khách hàng
CUSTOMER_POLICIES = {
    "normal": {"discount": 0, "free_shipping": False},
    "gold": {"discount": 0.05, "free_shipping": False},
    "vip": {"discount": 0.10, "free_shipping": True},
    "diamond": {"discount": 0.20, "free_shipping": True},
}

processed_orders = []
processing_log = []


class OrderManager:
    def __init__(self, order_date=DEFAULT_ORDER_DATE):
        self.order_date = order_date

    # Tính tổng tiền hàng
    def calculate_subtotal(self, items):
        subtotal = 0

        for item in items:
            if item["qty"] <= 0:
                print("loi so luong")
                return None

            subtotal += item["price"] * item["qty"]

        return subtotal

    # Tính phí vận chuyển
    def calculate_shipping(
        self, amount, shipping_type, free_shipping
    ):
        if free_shipping:
            return 0

        if shipping_type == SHIPPING_STANDARD:
            if amount >= FREE_SHIPPING_FROM:
                return 0
            return SHIPPING_TYPE_1_FEE

        if shipping_type == SHIPPING_EXPRESS:
            if amount >= FREE_SHIPPING_FROM:
                return SHIPPING_TYPE_2_FEE_HIGH
            return SHIPPING_TYPE_2_FEE_LOW

        return 0

    # Lưu đơn hàng ra file
    def save_order(self, order):
        try:
            with open(ORDER_FILE, "a", encoding="utf-8") as file:
                file.write(
                    f'{order["id"]},{order["total"]}\n'
                )
        except OSError as error:
            print("loi ghi file:", error)

    # Xử lý đơn hàng
    def process(self, order, shipping_type, send_email=False):
        if order is None:
            print("don hang None")
            return None

        if len(order["items"]) == 0:
            print("don hang rong")
            return None

        customer_type = order["customer"]["type"]

        if customer_type not in CUSTOMER_POLICIES:
            print("loai khach hang khong hop le")
            return None

        subtotal = self.calculate_subtotal(order["items"])

        if subtotal is None:
            return None

        policy = CUSTOMER_POLICIES[customer_type]

        discount = subtotal * policy["discount"]
        after_discount = subtotal - discount

        shipping_fee = self.calculate_shipping(
            after_discount,
            shipping_type,
            policy["free_shipping"],
        )

        tax = after_discount * TAX_RATE
        total = after_discount + shipping_fee + tax

        order["total"] = round(total)
        order["date"] = self.order_date.isoformat()

        processed_orders.append(order)
        processing_log.append("processed " + str(order["id"]))

        if send_email:
            print(
                f'Gui email toi {order["customer"]["email"]}: '
                f'Don hang {order["id"]} tong tien {order["total"]}'
            )

        self.save_order(order)

        return order["total"]

    # Thống kê đơn hàng
    def report(self):
        total_revenue = 0

        for order in processed_orders:
            total_revenue += order["total"]

        print("Tong so don: " + str(len(processed_orders)))
        print("Tong doanh thu: " + str(total_revenue))

        vip_revenue = 0
        vip_count = 0

        for order in processed_orders:
            if order["customer"]["type"] == "vip":
                vip_revenue += order["total"]
                vip_count += 1

        print("So don VIP: " + str(vip_count))
        print("Doanh thu VIP: " + str(vip_revenue))


if __name__ == "__main__":
    manager = OrderManager()

    manager.process(
        {
            "id": 1,
            "customer": {"type": "normal", "email": "a@x.com"},
            "items": [
                {"price": 100000, "qty": 2},
                {"price": 50000, "qty": 1},
            ],
        },
        SHIPPING_STANDARD,
        True,
    )

    manager.process(
        {
            "id": 2,
            "customer": {"type": "gold", "email": "b@x.com"},
            "items": [{"price": 300000, "qty": 2}],
        },
        SHIPPING_EXPRESS,
        False,
    )

    manager.process(
        {
            "id": 3,
            "customer": {"type": "vip", "email": "c@x.com"},
            "items": [{"price": 1000000, "qty": 1}],
        },
        SHIPPING_EXPRESS,
        True,
    )

    manager.process(
        {
            "id": 4,
            "customer": {"type": "silver", "email": "d@x.com"},
            "items": [{"price": 10000, "qty": 1}],
        },
        SHIPPING_STANDARD,
    )

    manager.process(
        {
            "id": 5,
            "customer": {"type": "normal", "email": "e@x.com"},
            "items": [],
        },
        SHIPPING_STANDARD,
    )

    manager.report()
