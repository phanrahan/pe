import pe 

def test_and():
    a = pe.and_()
    res, res_p = a(1,3)
    assert res==1
    assert res_p==0

def test_or():
    a = pe.or_()
    res, res_p = a(1,3)
    assert res==3
    assert res_p==0

def test_xor():
    a = pe.xor()
    res, res_p = a(1,3)
    assert res==2
    assert res_p==0

def test_inv():
    a = pe.inv()
    res, res_p = a(1)
    assert res==0xfffe
    assert res_p==0



