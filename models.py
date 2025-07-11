import hashlib
from datetime import datetime, timedelta

class Usuario:
    """Clase que maneja la lógica de negocio para los usuarios."""
    @staticmethod
    def hashPassword(password):
        """Genera un hash SHA256 para una contraseña dada."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verifyCredentials(dbConnection, username, password):
        """Verifica si el usuario y la contraseña coinciden con un registro en la BD."""
        cursor = dbConnection.cursor()
        cursor.execute("SELECT passwordHash, role FROM usuarios WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result and result[0] == Usuario.hashPassword(password):
            return result[1] # Devuelve el rol si las credenciales son correctas
        return None

    @staticmethod
    def create(dbConnection, username, password, role):
        """Crea un nuevo usuario en la base de datos."""
        if not all([username, password, role]):
            raise ValueError("Todos los campos son requeridos.")
        if role not in ['admin', 'cajero']:
            raise ValueError("El rol debe ser 'admin' o 'cajero'.")
        try:
            cursor = dbConnection.cursor()
            cursor.execute("INSERT INTO usuarios (username, passwordHash, role) VALUES (?, ?, ?)", (username, Usuario.hashPassword(password), role))
            dbConnection.commit()
        except dbConnection.IntegrityError:
            raise ValueError(f"El nombre de usuario '{username}' ya existe.")

    @staticmethod
    def update(dbConnection, userId, username, password, role):
        """Actualiza los datos de un usuario. Si la contraseña está vacía, no se modifica."""
        if not all([username, role]):
            raise ValueError("El nombre de usuario y el rol son requeridos.")
        if role not in ['admin', 'cajero']:
            raise ValueError("El rol debe ser 'admin' o 'cajero'.")
        try:
            cursor = dbConnection.cursor()
            if password:
                cursor.execute("UPDATE usuarios SET username = ?, passwordHash = ?, role = ? WHERE idUsuario = ?", (username, Usuario.hashPassword(password), role, userId))
            else:
                cursor.execute("UPDATE usuarios SET username = ?, role = ? WHERE idUsuario = ?", (username, role, userId))
            dbConnection.commit()
        except dbConnection.IntegrityError:
            raise ValueError(f"El nombre de usuario '{username}' ya pertenece a otro usuario.")

    @staticmethod
    def delete(dbConnection, userId):
        """Elimina un usuario por su ID."""
        cursor = dbConnection.cursor()
        cursor.execute("DELETE FROM usuarios WHERE idUsuario = ?", (userId,))
        dbConnection.commit()
        
    @staticmethod
    def getAll(dbConnection):
        """Obtiene una lista de todos los usuarios (sin sus contraseñas)."""
        cursor = dbConnection.cursor()
        cursor.execute("SELECT idUsuario, username, role FROM usuarios")
        return cursor.fetchall()

    @staticmethod
    def createDefaultAdminIfNeeded(dbConnection):
        """Si no hay usuarios en la BD, crea un usuario 'admin' con contraseña 'admin'."""
        cursor = dbConnection.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            Usuario.create(dbConnection, "admin", "admin", "admin")
            print("Usuario 'admin' por defecto creado con contraseña 'admin'.")

# ---------------------------------------------------------------------------

class Categoria:
    """Clase que maneja la lógica de negocio para las categorías de productos."""
    @staticmethod
    def create(dbConnection, nombre):
        try:
            cursor = dbConnection.cursor()
            cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
            dbConnection.commit()
        except dbConnection.IntegrityError:
            raise ValueError(f"La categoría '{nombre}' ya existe.")

    @staticmethod
    def getAll(dbConnection):
        cursor = dbConnection.cursor()
        cursor.execute("SELECT idCategoria, nombre FROM categorias ORDER BY nombre")
        return cursor.fetchall()

# ---------------------------------------------------------------------------

class Producto:
    """Clase para todas las operaciones relacionadas con el inventario de productos."""
    @staticmethod
    def getAll(dbConnection, categoriaId=None):
        """Obtiene todos los productos, opcionalmente filtrados por categoría."""
        cursor = dbConnection.cursor()
        query = "SELECT p.idProducto, p.codigoBarras, p.nombre, IFNULL(c.nombre, 'Sin Categoría'), p.precioVenta, p.costoCompra, p.stock FROM productos p LEFT JOIN categorias c ON p.idCategoria = c.idCategoria"
        params = []
        if categoriaId:
            query += " WHERE p.idCategoria = ?"
            params.append(categoriaId)
        query += " ORDER BY p.nombre"
        cursor.execute(query, params)
        return cursor.fetchall()
    
    @staticmethod
    def searchInventory(dbConnection, term):
        """Busca productos en el inventario por nombre o código de barras."""
        cursor = dbConnection.cursor()
        query = """
            SELECT p.idProducto, p.codigoBarras, p.nombre, IFNULL(c.nombre, 'Sin Categoría'), 
                   p.precioVenta, p.costoCompra, p.stock 
            FROM productos p 
            LEFT JOIN categorias c ON p.idCategoria = c.idCategoria
            WHERE p.nombre LIKE ? OR p.codigoBarras LIKE ?
            ORDER BY p.nombre
        """
        cursor.execute(query, (f"%{term}%", f"%{term}%"))
        return cursor.fetchall()

    @staticmethod
    def getLowStock(dbConnection, limit=5):
        """Obtiene una lista de productos con stock bajo o igual al límite especificado."""
        cursor = dbConnection.cursor()
        cursor.execute("""
            SELECT p.idProducto, p.codigoBarras, p.nombre, IFNULL(c.nombre, 'Sin Categoría'), p.stock 
            FROM productos p 
            LEFT JOIN categorias c ON p.idCategoria = c.idCategoria
            WHERE p.stock <= ? AND p.nombre != 'Recarga Celular'
            ORDER BY p.stock ASC
        """, (limit,))
        return cursor.fetchall()

    @staticmethod
    def getByBarcode(dbConnection, barcode):
        """Busca un producto específico por su código de barras."""
        cursor = dbConnection.cursor()
        query = "SELECT p.*, IFNULL(c.nombre, 'Sin Categoría') as categoriaNombre FROM productos p LEFT JOIN categorias c ON p.idCategoria = c.idCategoria WHERE p.codigoBarras = ?"
        cursor.execute(query, (barcode,))
        fila = cursor.fetchone()
        if fila:
            column_names = [description[0] for description in cursor.description]
            return dict(zip(column_names, fila))
        return None

    @staticmethod
    def getById(dbConnection, productoId):
        """Obtiene los datos completos de un producto por su ID."""
        cursor = dbConnection.cursor()
        query = "SELECT p.*, IFNULL(c.nombre, 'Sin Categoría') as categoriaNombre FROM productos p LEFT JOIN categorias c ON p.idCategoria = c.idCategoria WHERE p.idProducto = ?"
        cursor.execute(query, (productoId,))
        fila = cursor.fetchone()
        if fila:
            column_names = [description[0] for description in cursor.description]
            return dict(zip(column_names, fila))
        return None

    @staticmethod
    def searchByName(dbConnection, partialName):
        """Busca productos por una coincidencia parcial en el nombre."""
        cursor = dbConnection.cursor()
        query = "SELECT p.*, IFNULL(c.nombre, 'Sin Categoría') as categoriaNombre FROM productos p LEFT JOIN categorias c ON p.idCategoria = c.idCategoria WHERE p.nombre LIKE ? ORDER BY nombre"
        cursor.execute(query, (f"%{partialName}%",))
        filas = cursor.fetchall()
        if filas:
            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, fila)) for fila in filas]
        return []
    
    @staticmethod
    def create(dbConnection, codigoBarras, nombre, precioVenta, costoCompra, stock, idCategoria):
        """Crea un nuevo producto en la base de datos."""
        try:
            cursor = dbConnection.cursor()
            cursor.execute("INSERT INTO productos (codigoBarras, nombre, descripcion, precioVenta, costoCompra, stock, idCategoria) VALUES (?, ?, ?, ?, ?, ?, ?)", (codigoBarras, nombre, "", float(precioVenta), float(costoCompra), int(stock), idCategoria))
            dbConnection.commit()
        except dbConnection.IntegrityError: raise ValueError(f"El código de barras '{codigoBarras}' ya existe.")

    @staticmethod
    def update(dbConnection, productoId, codigoBarras, nombre, precioVenta, costoCompra, stock, idCategoria):
        """Actualiza los datos de un producto existente."""
        try:
            cursor = dbConnection.cursor()
            cursor.execute("UPDATE productos SET codigoBarras=?, nombre=?, precioVenta=?, costoCompra=?, stock=?, idCategoria=? WHERE idProducto=?", (codigoBarras, nombre, precioVenta, costoCompra, stock, idCategoria, productoId))
            dbConnection.commit()
        except dbConnection.IntegrityError: raise ValueError(f"El código de barras '{codigoBarras}' ya pertenece a otro producto.")

    @staticmethod
    def delete(dbConnection, productoId):
        """Elimina un producto de la base de datos."""
        cursor = dbConnection.cursor()
        cursor.execute("DELETE FROM productos WHERE idProducto = ?", (productoId,))
        dbConnection.commit()

    @staticmethod
    def updateStock(dbConnection, productoId, cantidad):
        """Ajusta el stock de un producto. Usa valores negativos para decrementos (ventas)."""
        cursor = dbConnection.cursor()
        cursor.execute("UPDATE productos SET stock = stock + ? WHERE idProducto = ?", (cantidad, productoId))
        dbConnection.commit()

    @staticmethod
    def populateInitialProducts(dbConnection):
        cursor = dbConnection.cursor()
        cursor.execute("SELECT COUNT(*) FROM productos")
        if cursor.fetchone()[0] > 0: return
        
        # Crear categoría de dulces y obtener su ID
        try:
            Categoria.create(dbConnection, "Dulces")
        except ValueError:
            pass # La categoría ya existe
        
        cursor.execute("SELECT idCategoria FROM categorias WHERE nombre = 'Dulces'")
        id_dulces_result = cursor.fetchone()
        id_dulces = id_dulces_result[0] if id_dulces_result else None


        productosIniciales = [
            ("7501031310017", "Lápiz HB #2", "Lápiz de grafito para escritura general", 3.50, 1.50, 100, "Papelería"),
            ("7501031310024", "Cuaderno Profesional 100 Hojas Raya", "Cuaderno de 100 hojas a raya", 25.00, 12.00, 50, "Papelería"),
            ("7501031310031", "Borrador de Goma", "Borrador de goma blanco, no mancha", 4.00, 2.00, 75, "Papelería"),
            ("7501031310048", "Celomágico Mediano Adhesivo (Adosa)", "Cinta adhesiva mágica, acabado mate, 50 yardas", 30.00, 15.00, 40, "Papelería"),
            ("7501031310055", "Euroformas Cuaderno Profesional 5x8", "Cuaderno profesional de 5x8 pulgadas", 28.00, 13.00, 35, "Papelería"),
        ]
        try:
            cursor.executemany("INSERT INTO productos (codigoBarras, nombre, descripcion, precioVenta, costoCompra, stock, idCategoria) VALUES (?, ?, ?, ?, ?, ?, ?)", productosIniciales)
            dbConnection.commit()
            print("Productos iniciales insertados.")
        except dbConnection.IntegrityError: pass

# ---------------------------------------------------------------------------

class Venta:
    """Clase para la lógica de ventas y la generación de reportes financieros."""
    @staticmethod
    def create(dbConnection, carrito, metodoPago, descuento):
        """
        Registra una nueva venta, sus detalles y actualiza el stock de los productos vendidos.
        Devuelve el ID de la venta creada.
        """
        cursor = dbConnection.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subtotal = sum(item['subtotal'] for item in carrito)
        total = subtotal - descuento
        
        cursor.execute("INSERT INTO ventas (fecha, subtotal, descuento, totalVenta, metodoPago) VALUES (?, ?, ?, ?, ?)", (fecha, subtotal, descuento, total, metodoPago))
        ventaId = cursor.lastrowid
        
        for item in carrito:
            cursor.execute("INSERT INTO detallesVenta (idVenta, idProducto, cantidad, precioUnitario, subtotal) VALUES (?, ?, ?, ?, ?)", (ventaId, item['id'], item['cantidad'], item['precio'], item['subtotal']))
            # Las recargas no descuentan stock del inventario físico
            if not item['nombre'].startswith("Recarga Celular"):
                 Producto.updateStock(dbConnection, item['id'], -item['cantidad'])

        dbConnection.commit()
        return ventaId

    @staticmethod
    def getById(dbConnection, ventaId):
        """Obtiene todos los datos de una venta, incluyendo sus detalles, por su ID."""
        cursor = dbConnection.cursor()
        cursor.execute("SELECT * FROM ventas WHERE idVenta = ?", (ventaId,))
        venta = cursor.fetchone()
        if not venta: return None

        column_names = [d[0] for d in cursor.description]
        ventaData = dict(zip(column_names, venta))

        cursor.execute("SELECT dv.*, p.nombre FROM detallesVenta dv JOIN productos p ON dv.idProducto = p.idProducto WHERE dv.idVenta = ?", (ventaId,))
        detalles = cursor.fetchall()
        
        column_names_detalles = [d[0] for d in cursor.description]
        ventaData['detalles'] = [dict(zip(column_names_detalles, d)) for d in detalles]
        return ventaData

    @staticmethod
    def get_date_range(periodo):
        """Función de ayuda para obtener las fechas de inicio y fin según un período ('dia', 'semana', 'mes')."""
        hoy = datetime.now()
        if periodo == 'dia':
            start_date = hoy.strftime('%Y-%m-%d')
            end_date = start_date
        elif periodo == 'semana':
            start_date = (hoy - timedelta(days=hoy.weekday())).strftime('%Y-%m-%d')
            end_date = hoy.strftime('%Y-%m-%d')
        elif periodo == 'mes':
            start_date = hoy.strftime('%Y-%m-01')
            end_date = hoy.strftime('%Y-%m-%d')
        else:
            return None, None
        return f'{start_date} 00:00:00', f'{end_date} 23:59:59'

    @staticmethod
    def getReporteVentas(dbConnection, periodo):
        """
        Genera un reporte de ventas simple para un período dado.
        Calcula totales brutos, netos, descuentos, devoluciones y los productos más vendidos.
        """
        start, end = Venta.get_date_range(periodo)
        cursor = dbConnection.cursor()
        
        cursor.execute("SELECT COALESCE(SUM(totalVenta), 0), COALESCE(SUM(descuento), 0), COUNT(idVenta) FROM ventas WHERE fecha BETWEEN ? AND ?", (start, end))
        totalNeto, totalDesc, numTickets = cursor.fetchone()
        
        cursor.execute("SELECT COALESCE(SUM(montoDevuelto), 0) FROM devoluciones WHERE fecha BETWEEN ? AND ?", (start, end))
        totalDevoluciones = cursor.fetchone()[0]

        totalBruto = totalNeto + totalDesc
        ventasNetasFinal = totalNeto - totalDevoluciones
        
        cursor.execute("""
            SELECT p.nombre, SUM(dv.cantidad) as total_vendido
            FROM detallesVenta dv
            JOIN ventas v ON dv.idVenta = v.idVenta
            JOIN productos p ON dv.idProducto = p.idProducto
            WHERE v.fecha BETWEEN ? AND ? AND p.nombre != 'Recarga Celular'
            GROUP BY p.idProducto ORDER BY total_vendido DESC LIMIT 5
        """, (start, end))
        productosMasVendidos = cursor.fetchall()

        return {
            'totalBruto': totalBruto, 'totalDescuentos': totalDesc, 'totalDevoluciones': totalDevoluciones,
            'ventasNetas': ventasNetasFinal, 'numTickets': numTickets, 'productosMasVendidos': productosMasVendidos
        }

    @staticmethod
    def getReporteGanancias(dbConnection, periodo):
        """
        Genera un reporte financiero detallado, calculando la ganancia neta estimada.
        Considera ingresos, costos de productos, descuentos, devoluciones y otros gastos.
        """
        start, end = Venta.get_date_range(periodo)
        cursor = dbConnection.cursor()
        # Ingresos
        cursor.execute("SELECT COALESCE(SUM(totalVenta), 0), COALESCE(SUM(descuento), 0) FROM ventas WHERE fecha BETWEEN ? AND ?", (start, end))
        ingresosNetos, totalDesc = cursor.fetchone()
        ingresosBrutos = ingresosNetos + totalDesc
        # Costo de mercancía vendida (excluyendo recargas)
        cursor.execute("""
            SELECT COALESCE(SUM(dv.cantidad * p.costoCompra), 0)
            FROM detallesVenta dv JOIN productos p ON dv.idProducto = p.idProducto
            WHERE dv.idVenta IN (SELECT idVenta FROM ventas WHERE fecha BETWEEN ? AND ?) AND p.nombre != 'Recarga Celular'
        """, (start, end))
        costosTotales = cursor.fetchone()[0]
        # Ganancia e ingresos por recargas
        cursor.execute("""
            SELECT COALESCE(SUM(dv.cantidad), 0) FROM detallesVenta dv JOIN productos p ON dv.idProducto = p.idProducto
            WHERE dv.idVenta IN (SELECT idVenta FROM ventas WHERE fecha BETWEEN ? AND ?) AND p.nombre = 'Recarga Celular'
        """, (start, end))
        gananciaRecargas = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(dv.subtotal), 0) FROM detallesVenta dv JOIN productos p ON dv.idProducto = p.idProducto
            WHERE dv.idVenta IN (SELECT idVenta FROM ventas WHERE fecha BETWEEN ? AND ?) AND p.nombre = 'Recarga Celular'
        """, (start, end))
        ingresoTotalRecargas = cursor.fetchone()[0]
        # Egresos (devoluciones y gastos)
        cursor.execute("SELECT COALESCE(SUM(montoDevuelto), 0) FROM devoluciones WHERE fecha BETWEEN ? AND ?", (start, end))
        totalDevoluciones = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(monto), 0) FROM gastos WHERE DATE(fecha) BETWEEN ? AND ?", (start.split(' ')[0], end.split(' ')[0]))
        totalGastos = cursor.fetchone()[0]
        return {
            'ingresosBrutos': ingresosBrutos, 'costosTotales': costosTotales,
            'totalDescuentos': totalDesc, 'totalDevoluciones': totalDevoluciones,
            'totalGastos': totalGastos, 'gananciaRecargas': gananciaRecargas,
            'ingresoTotalRecargas': ingresoTotalRecargas
        }
        
    @staticmethod
    def getDashboardData(dbConnection):
        """Obtiene los datos clave para las tarjetas de resumen del dashboard (ventas de hoy, tickets, etc.)."""
        start, end = Venta.get_date_range('dia')
        cursor = dbConnection.cursor()
        cursor.execute("SELECT COALESCE(SUM(totalVenta), 0), COUNT(idVenta) FROM ventas WHERE fecha BETWEEN ? AND ?", (start, end))
        ventasHoy, ticketsHoy = cursor.fetchone()
        cursor.execute("SELECT COUNT(idProducto) FROM productos WHERE stock <= 5 AND nombre != 'Recarga Celular'")
        bajoStock = cursor.fetchone()[0]
        return {'ventasNetasHoy': ventasHoy, 'numTicketsHoy': ticketsHoy, 'productosBajoStock': bajoStock}

    @staticmethod
    def getVentasUltimosDias(dbConnection, dias=7):
        """
        Calcula las ventas totales para cada uno de los últimos 'dias'.
        Devuelve un diccionario con abreviaturas de días de la semana en español como claves.
        """
        ventas = {}
        dias_es = {"Mon": "Lun", "Tue": "Mar", "Wed": "Mié", "Thu": "Jue", "Fri": "Vie", "Sat": "Sáb", "Sun": "Dom"}
        hoy = datetime.now()
        
        for i in range(dias):
            fecha_dt = hoy - timedelta(days=i)
            fecha_str = fecha_dt.strftime('%Y-%m-%d')
            
            cursor = dbConnection.cursor()
            cursor.execute("SELECT COALESCE(SUM(totalVenta), 0) FROM ventas WHERE DATE(fecha) = ?", (fecha_str,))
            total = cursor.fetchone()[0]
            
            dia_semana_en = fecha_dt.strftime('%a')
            dia_semana_es = dias_es.get(dia_semana_en, dia_semana_en)
            
            ventas[dia_semana_es] = total
            
        # Devuelve el diccionario en orden cronológico (los días más antiguos primero)
        return dict(reversed(list(ventas.items())))

    @staticmethod
    def getVentasPorCategoria(dbConnection, periodo):
        """Obtiene el total de ingresos agrupado por categoría para un período dado."""
        start, end = Venta.get_date_range(periodo)
        cursor = dbConnection.cursor()
        cursor.execute("""
            SELECT IFNULL(c.nombre, 'Sin Categoría'), SUM(dv.subtotal) 
            FROM detallesVenta dv
            JOIN productos p ON dv.idProducto = p.idProducto
            LEFT JOIN categorias c ON p.idCategoria = c.idCategoria
            JOIN ventas v ON dv.idVenta = v.idVenta
            WHERE v.fecha BETWEEN ? AND ?
            GROUP BY c.nombre HAVING SUM(dv.subtotal) > 0.01
            ORDER BY SUM(dv.subtotal) DESC
        """, (start, end))
        return cursor.fetchall()
        
    @staticmethod
    def getTopProductos(dbConnection, periodo, limit=5):
        """Obtiene los productos más vendidos por ingresos en un período."""
        start, end = Venta.get_date_range(periodo)
        cursor = dbConnection.cursor()
        cursor.execute("""
            SELECT p.nombre, SUM(dv.subtotal) as total
            FROM detallesVenta dv
            JOIN productos p ON dv.idProducto = p.idProducto
            JOIN ventas v ON dv.idVenta = v.idVenta
            WHERE v.fecha BETWEEN ? AND ?
            GROUP BY p.nombre ORDER BY total DESC LIMIT ?
        """, (start, end, limit))
        return cursor.fetchall()

    @staticmethod
    def getLibroDiario(dbConnection, periodo):
        """Combina ventas, gastos y devoluciones en un solo historial cronológico (libro diario)."""
        start, end = Venta.get_date_range(periodo)
        cursor = dbConnection.cursor()
        query = f"""
            SELECT fecha, 'Venta Ticket #' || idVenta, totalVenta, 'venta', idVenta FROM ventas WHERE fecha BETWEEN ? AND ?
            UNION ALL
            SELECT fecha, 'Gasto: ' || descripcion, -monto, 'gasto', idGasto FROM gastos WHERE fecha BETWEEN ? AND ?
            UNION ALL
            SELECT fecha, 'Devolución de Venta #' || idVentaOriginal, -montoDevuelto, 'devolucion', idDevolucion FROM devoluciones WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
        """
        start_date, end_date = start.split(' ')[0], end.split(' ')[0]
        params = (start, end, f"{start_date} 00:00:00", f"{end_date} 23:59:59", start, end)
        cursor.execute(query, params)
        return cursor.fetchall()

# ---------------------------------------------------------------------------

class Devolucion:
    """Clase para manejar la lógica de las devoluciones."""
    @staticmethod
    def create(dbConnection, idVentaOriginal, items):
        """
        Registra una devolución, detallando los productos y el monto.
        Actualiza (incrementa) el stock de los productos devueltos.
        """
        cursor = dbConnection.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in items:
            cursor.execute("""
                INSERT INTO devoluciones (idVentaOriginal, idProducto, cantidad, montoDevuelto, fecha)
                VALUES (?, ?, ?, ?, ?)
            """, (idVentaOriginal, item['idProducto'], item['cantidad'], item['montoDevuelto'], fecha))
            # Las recargas no se devuelven al stock.
            if not item['nombreProducto'].startswith("Recarga Celular"):
                Producto.updateStock(dbConnection, item['idProducto'], item['cantidad'])
        dbConnection.commit()

# ---------------------------------------------------------------------------

class Gasto:
    """Clase para manejar la lógica de los gastos operativos."""
    @staticmethod
    def create(dbConnection, descripcion, monto):
        """Registra un nuevo gasto en la base de datos."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = dbConnection.cursor()
        cursor.execute("INSERT INTO gastos (fecha, descripcion, monto) VALUES (?, ?, ?)", (fecha, descripcion, monto))
        dbConnection.commit()

    @staticmethod
    def getByDate(dbConnection, fecha):
        """Obtiene todos los gastos registrados en una fecha específica."""
        cursor = dbConnection.cursor()
        cursor.execute("SELECT idGasto, fecha, descripcion, monto FROM gastos WHERE DATE(fecha) = ? ORDER BY fecha DESC", (fecha,))
        return cursor.fetchall()

    @staticmethod
    def delete(dbConnection, gastoId):
        """Elimina un gasto por su ID."""
        cursor = dbConnection.cursor()
        cursor.execute("DELETE FROM gastos WHERE idGasto = ?", (gastoId,))
        dbConnection.commit()