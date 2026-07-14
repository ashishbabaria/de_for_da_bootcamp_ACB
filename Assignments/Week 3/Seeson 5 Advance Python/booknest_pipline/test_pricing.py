from pricing import member_price, add_gst, delivery_fee, loyalty_points
 
 
# ---------- member_price ----------
 
def test_member_price_ten_percent():
    assert member_price(1000, 10) == 900
 
 
def test_member_price_zero_discount():
    assert member_price(500, 0) == 500
 
 
def test_member_price_full_discount():
    assert member_price(250, 100) == 0
 
 
# ---------- add_gst ----------
 
def test_add_gst_default_rate():
    assert add_gst(1000) == 1050          # default 5% for books
 
 
def test_add_gst_custom_rate():
    assert add_gst(1000, 18) == 1180
 
 
def test_add_gst_zero_price():
    assert add_gst(0) == 0
 
 
# ---------- delivery_fee ----------
 
def test_delivery_fee_above_threshold():
    assert delivery_fee(600) == 0
 
 
def test_delivery_fee_below_threshold():
    assert delivery_fee(300) == 40
 
 
def test_delivery_fee_exactly_at_threshold():
    # boundary case: free_above=500, order_total=500 should be free ( >= )
    assert delivery_fee(500) == 0
 
 
def test_delivery_fee_custom_threshold():
    assert delivery_fee(150, free_above=200, flat=25) == 25
 
 
# ---------- loyalty_points ----------
 
def test_loyalty_points_whole_hundreds():
    assert loyalty_points(950) == 9
 
 
def test_loyalty_points_under_hundred():
    assert loyalty_points(99) == 0
 
 
def test_loyalty_points_exact_hundred():
    assert loyalty_points(100) == 1