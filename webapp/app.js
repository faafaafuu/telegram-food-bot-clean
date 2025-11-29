// Современный SPA-фронт Jafood, адаптированный под Telegram WebApp и мобильные устройства
const { useState, useEffect } = React;

function fetchJson(url, opts) {
  return fetch(url, opts).then(r => r.json());
}

function CategoryList({ categories, selected, onSelect }) {
  return (
    <div className="categories">
      {categories.map(cat => (
        <button
          key={cat.id}
          className={selected === cat.id ? "selected" : ""}
          onClick={() => onSelect(cat.id)}
        >
          {cat.title || cat.name}
        </button>
      ))}
    </div>
  );
}

function ProductCard({ product, onAdd, onDetails }) {
  const [qty, setQty] = useState(1);
  return (
    <div className="product-card">
      <img src={product.image || "https://dodopizza.ru/static/Img/Products/pizza/ru-RU/1c7e3e2e-7e2e-4e2e-8e2e-2e2e2e2e2e2e.jpg"} alt={product.name} />
      <div className="product-info">
        <h3>{product.name}</h3>
        <p>{product.description}</p>
        <div className="product-bottom">
          <span className="price">{product.price} ₽</span>
          <input type="number" min="1" max="20" value={qty} style={{width:'2.5em'}} onChange={e => setQty(Math.max(1, +e.target.value))} />
          <button onClick={() => onAdd({...product, qty})}>+</button>
        </div>
        <button style={{marginTop:6,background:'#eee',color:'#333',border:'none',borderRadius:8,padding:'4px 10px'}} onClick={() => onDetails(product)}>Подробнее</button>
      </div>
    </div>
  );
}

function CartBar({ items, onOrder }) {
  const total = items.reduce((sum, i) => sum + i.price * i.qty, 0);
  return (
    <div className="cart-bar">
      <span>Корзина: {items.length} • {total} ₽</span>
      <button disabled={!items.length} onClick={onOrder}>Оформить</button>
    </div>
  );
}

function App() {
  const [categories, setCategories] = useState([]);
  const [selectedCat, setSelectedCat] = useState(null);
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(false);
  const [orderStatus, setOrderStatus] = useState("");
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [modalProduct, setModalProduct] = useState(null);

  const [catError, setCatError] = useState("");
  const [prodError, setProdError] = useState("");

  useEffect(() => {
    fetchJson("/api/categories")
      .then(data => {
        setCategories(data);
        setCatError("");
        if (data.length) setSelectedCat(data[0].id);
      })
      .catch(e => setCatError("Ошибка загрузки категорий: " + e));
  }, []);

  useEffect(() => {
    if (selectedCat) {
      setLoading(true);
      fetchJson(`/api/products?category_id=${selectedCat}`)
        .then(data => { setProducts(data); setProdError(""); setLoading(false); })
        .catch(e => { setProdError("Ошибка загрузки позиций: " + e); setLoading(false); });
    }
  }, [selectedCat]);

  function addToCart(product) {
    setCart(prev => {
      const idx = prev.findIndex(i => i.id === product.id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx].qty += product.qty || 1;
        return copy;
      }
      return [...prev, { ...product, qty: product.qty || 1 }];
    });
  }

  function removeFromCart(id) {
    setCart(prev => prev.filter(i => i.id !== id));
  }

  function order() {
    setShowOrderModal(true);
  }

  function confirmOrder() {
    setShowOrderModal(false);
    setCart([]);
    setOrderStatus("Заказ оформлен! Ожидайте подтверждения.");
    setTimeout(() => setOrderStatus("");, 3000);
  }

  return (
    <div className="main">
      <header>
        <h1>Jafood — меню</h1>
      </header>
      {catError && <div style={{color:'red',padding:'8px'}}>{catError}</div>}
      <CategoryList categories={categories} selected={selectedCat} onSelect={setSelectedCat} />
      <div className="content">
        <div className="products">
          {prodError && <div style={{color:'red',padding:'8px'}}>{prodError}</div>}
          {loading ? <p>Загрузка...</p> : products.length === 0 ? <p>Нет позиций</p> : (
            products.map(p => <ProductCard key={p.id} product={p} onAdd={addToCart} onDetails={setModalProduct} />)
          )}
        </div>
      </div>
      <CartBar items={cart} onOrder={order} />
      {showOrderModal && (
        <div className="modal" onClick={() => setShowOrderModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Оформление заказа</h2>
            <input type="text" placeholder="Ваше имя" />
            <input type="tel" placeholder="Телефон" />
            <button onClick={confirmOrder}>Отправить заказ</button>
          </div>
        </div>
      )}
      {modalProduct && (
        <div className="modal" onClick={() => setModalProduct(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>{modalProduct.name}</h2>
            <img src={modalProduct.image || "https://dodopizza.ru/static/Img/Products/pizza/ru-RU/1c7e3e2e-7e2e-4e2e-8e2e-2e2e2e2e2e2e.jpg"} alt={modalProduct.name} style={{width:'100%',borderRadius:'12px'}} />
            <p>{modalProduct.description}</p>
            <div style={{marginTop:'12px'}}>
              <span className="price">{modalProduct.price} ₽</span>
              <button style={{marginLeft:'12px'}} onClick={()=>{ addToCart(modalProduct); setModalProduct(null); }}>В корзину</button>
            </div>
            <button style={{marginTop:'18px',background:'#eee',color:'#333',border:'none',borderRadius:8,padding:'8px 12px'}} onClick={()=>setModalProduct(null)}>Закрыть</button>
          </div>
        </div>
      )}
      {orderStatus && <div className="order-status">{orderStatus}</div>}
      <footer>
        <small>Демо-версия. Дизайн вдохновлён Додо Пиццей.</small>
      </footer>
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById("root"));
  React.useEffect(()=>{ loadCategories() }, [])

  async function loadCategories(){
    const res = await fetch(API_BASE + '/categories')
    const data = await res.json()
    setCategories(data)
    if(data.length) selectCat(data[0].id)
  }

  async function selectCat(id){
    setActiveCat(id)
    const res = await fetch(API_BASE + '/products?category_id=' + id)
    const data = await res.json()
    setProducts(data)
  }

  function addToCart(p){
    setCart(prev=>{
      const copy = [...prev]
      const ex = copy.find(i=>i.product_id===p.id)
      if(ex) ex.qty += 1
      else copy.push({product_id:p.id, qty:1, name:p.name, price:p.price})
      return copy
    })
  }

  async function checkout(){
    // create order
    const order = {tg_id:0, items: cart, total_price: cart.reduce((s,i)=>s+i.price*i.qty,0), payment_method:'online'}
    const res = await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(order)})
    const data = await res.json()
    // open payment page
    window.open(data.payment_url + '')
    alert('Order created; opening payment')
    setCart([])
  }

  return html`<div id='app' style=${{padding:12}}>
    <header style=${{display:'flex',alignItems:'center',gap:12}}>
      <img src='' alt='logo' style=${{width:48,height:48,borderRadius:8,background:'#eee'}} />
      <h3>Ресторан</h3>
    </header>
    <div style=${{display:'flex',gap:8,overflow:'auto',padding:'8px 0'}}>
      ${categories.map(c=> html`<button key=${c.id} onClick=${()=>selectCat(c.id)} style=${{padding:8,borderRadius:8,background: c.id===activeCat? '#ddd':'#fff'}}>${c.title}</button>`)}
    </div>
    <div style=${{display:'grid',gridTemplateColumns:'repeat(2,1fr)',gap:8}}>
      ${products.map(p=> html`<div key=${p.id} style=${{border:'1px solid #eee',padding:8,borderRadius:8}}>
        <div style=${{height:120,background:'#fafafa',marginBottom:8}}></div>
        <h4>${p.name}</h4>
        <div style=${{fontSize:13,color:'#666'}}>${p.description||''}</div>
        <div style=${{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:8}}>
          <b>${p.price}₽</b>
          <div>
            <button onClick=${()=>addToCart(p)}>Добавить</button>
            <button onClick=${()=>setModalProduct(p)} style=${{marginLeft:6}}>Открыть</button>
          </div>
        </div>
      </div>`)}
    </div>

    <div style=${{position:'fixed',right:12,bottom:12}}>
      <button onClick=${()=>setView('cart')}>Корзина (${cart.reduce((s,i)=>s+i.qty,0)})</button>
    </div>

    ${view==='cart' && html`<div style=${{position:'fixed',left:0,top:0,right:0,bottom:0,background:'rgba(0,0,0,0.4)',display:'flex',alignItems:'center',justifyContent:'center'}} onClick=${()=>setView('menu')}>
      <div style=${{width:320,background:'#fff',padding:12,borderRadius:8}} onClick=${e=>e.stopPropagation()}>
        <h3>Корзина</h3>
        ${cart.length===0? html`<div>Пусто</div>` : cart.map(i=> html`<div style=${{display:'flex',justifyContent:'space-between',alignItems:'center'}}>${i.name} x${i.qty} <b>${i.price*i.qty}₽</b></div>`) }
        <div style=${{marginTop:8}}>Итого: <b>${cart.reduce((s,i)=>s+i.price*i.qty,0)}₽</b></div>
        <div style=${{marginTop:8}}>
          <button onClick=${checkout}>Оформить заказ</button>
          <button onClick=${()=>setView('menu')} style=${{marginLeft:8}}>Закрыть</button>
        </div>
      </div>
    </div>`}

    ${modalProduct && html`<div style=${{position:'fixed',left:0,top:0,right:0,bottom:0,background:'rgba(0,0,0,0.5)'}} onClick=${()=>setModalProduct(null)}>
      <div style=${{background:'#fff',width:320,margin:'50px auto',padding:12,borderRadius:8}} onClick=${e=>e.stopPropagation()}>
        <h3>${modalProduct.name}</h3>
        <div>${modalProduct.description}</div>
        <div style=${{marginTop:8}}><b>${modalProduct.price}₽</b></div>
        <div style=${{marginTop:8}}>
          <button onClick=${()=>{ addToCart(modalProduct); setModalProduct(null)}}>Добавить в корзину</button>
          <button onClick=${()=>setModalProduct(null)} style=${{marginLeft:8}}>Закрыть</button>
        </div>
      </div>
    </div>`}
  </div>`
}

ReactDOM.createRoot(document.getElementById('app')).render(html`<${App} />`)
