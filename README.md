# Sistema de Punto de Venta (POS) para Papelería

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

Este proyecto es una aplicación de escritorio de Punto de Venta (POS) completa, desarrollada en Python. El sistema está diseñado para optimizar y automatizar las operaciones diarias de un pequeño negocio minorista, centralizando la gestión de ventas, inventario, finanzas y usuarios en una interfaz gráfica intuitiva y funcional.

## 🚀 Características Principales

El sistema se organiza en módulos con control de acceso basado en roles (Administrador y Cajero).

#### **Módulo de Ventas (POS)**
* **Búsqueda Rápida:** Encuentra productos por código de barras o por coincidencias parciales en el nombre.
* **Carrito de Compras Dinámico:** Agrega, modifica la cantidad o elimina productos fácilmente.
* **Descuentos:** Aplica descuentos porcentuales al total de la venta.
* **Manejo de Casos Especiales:**
    * **Recargas Telefónicas:** Diálogo para seleccionar un monto variable, con una comisión fija.
    * **Dulces:** Diálogo especial para agregar múltiples tipos de dulces rápidamente.
* **Múltiples Métodos de Pago:** Acepta pagos en Efectivo (con cálculo de cambio) o Tarjeta.
* **Generación de Tickets:** Crea e imprime un ticket de compra detallado en formato PDF al finalizar cada venta.

#### **Panel de Administrador (Dashboard)**
* **Métricas en Tiempo Real:** Visualiza las ventas totales del día, el número de tickets y la cantidad de productos con bajo stock.
* **Gráficos Interactivos:**
    * Gráfico de barras con las ventas de los últimos 7 días.
    * Gráfico de dona mostrando la distribución de ingresos por categoría.
    * Gráfico de barras horizontales con el top 5 de productos más vendidos.
* **Navegación Centralizada:** Acceso rápido a todos los módulos de gestión.

#### **Gestión de Datos y Reportes**
* **Módulo de Inventario:**
    * CRUD completo de productos (Crear, Leer, Actualizar, Eliminar).
    * Sistema de reabastecimiento de stock.
    * Filtro por categorías y búsqueda integrada.
* **Módulo de Usuarios:**
    * CRUD completo de usuarios y asignación de roles.
* **Módulo Financiero:**
    * **Estado Financiero:** Calcula el balance de caja estimado (saldo inicial + ingresos - gastos - devoluciones).
    * **Reportes Avanzados:** Genera reportes de Ventas y Ganancias por día, semana o mes.
    * **Libro Diario:** Un registro cronológico de todas las transacciones (ventas, gastos, devoluciones).
    * **Control de Gastos:** Registra y elimina gastos operativos.
    * **Gestión de Devoluciones:** Procesa devoluciones basadas en un ticket de venta existente.

#### **Herramientas Administrativas**
* **Importación Masiva:** Carga productos en lote desde un formato de texto separado por comas.
* **Exportación de Datos:** Exporta el inventario completo a formatos **CSV** y **Excel (.xlsx)**.
* **Copias de Seguridad:** Crea y restaura la base de datos completa para prevenir la pérdida de datos.

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3
* **Interfaz Gráfica:** Tkinter
* **Base de Datos:** SQLite 3
* **Gráficos y Visualización:** Matplotlib
* **Generación de PDF:** FPDF2
* **Exportación a Excel:** OpenPyXL

## 🏛️ Decisiones de Arquitectura y Diseño

El proyecto se construyó sobre principios de software que garantizan su mantenibilidad, eficiencia y escalabilidad.

#### 1. Base de Datos Relacional (SQLite)
Se eligió **SQLite** porque es una base de datos ligera, sin servidor y basada en un único archivo (`pos.db`). Es la opción ideal para aplicaciones de escritorio como esta, ya que no requiere instalación ni configuración de un servicio de base de datos externo, facilitando la portabilidad y el despliegue.

#### 2. Separación de Responsabilidades (Modelo-Vista-Controlador implícito)
El código está estructurado para separar la lógica de la presentación:
* **Modelo (`models.py`, `database.py`):** Contiene toda la lógica de negocio y las interacciones con la base de datos. Se encarga de *qué* hace la aplicación.
* **Vista y Controlador (`main.py`):** Gestiona la interfaz gráfica y el flujo de eventos. Responde a la interacción del usuario y llama al modelo para realizar acciones. Se encarga de *cómo* se muestra y se interactúa con la aplicación.

Esta separación es fundamental para la **mantenibilidad**. Permite modificar la interfaz gráfica sin afectar la lógica de negocio, y viceversa.

#### 3. Estrategia de Búsqueda con `LIKE`
La búsqueda de productos se realiza con el operador `LIKE` de SQL en lugar de algoritmos en Python.
* **Experiencia de Usuario:** Permite búsquedas parciales y flexibles, lo cual es más intuitivo para el usuario final que una búsqueda exacta.
* **Rendimiento:** Delegar la búsqueda a la base de datos es mas eficiente. 

#### 4. Uso Estratégico de `LEFT JOIN`
Para obtener datos de tablas relacionadas (como el nombre de la categoría de un producto), se utiliza `LEFT JOIN`. Esto permite obtener toda la información necesaria en una única y eficiente consulta a la base de datos, en lugar de realizar múltiples consultas en un bucle, lo que podría degradar el rendimiento.
