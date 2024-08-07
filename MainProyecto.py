import math
import customtkinter as ctk
import os
import tkinter
from PIL import Image
from tkinter import filedialog
import pandas as pd
from CTkTable import CTkTable
from CTkTableRowSelector import CTkTableRowSelector
import tkintermapview
import pandas as pd
import sqlite3
import pyproj
from CTkMessagebox import CTkMessagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos en la Tierra especificados por su latitud y longitud usando la fórmula de Haversine.
    
    Parámetros:
    lat1, lon1: Latitud y longitud del primer punto en grados.
    lat2, lon2: Latitud y longitud del segundo punto en grados.
    
    Retorna:
    Distancia entre los dos puntos en kilómetros.
    """
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir las coordenadas de grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias de las coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distancia en kilómetros
    distance = R * c
    
    return distance
def ejecutar_query_sqlite(database_name, table_name, columns='*', where_column=None, where_value=None):
    """
    Ejecuta una consulta SQL en una base de datos SQLite y retorna una lista con los resultados.

    Parámetros:
    database_name (str): Nombre del archivo de la base de datos SQLite.
    table_name (str): Nombre de la tabla para realizar la consulta.
    columns (str): Columnas a seleccionar (por defecto es '*').
    where_column (str): Nombre de la columna para la cláusula WHERE (opcional).
    where_value (any): Valor para la cláusula WHERE (opcional).

    Retorna:
    list: Lista con los resultados de la consulta.
    List: Lista con el nombre de las columnas.
    """
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()

    # Crear la consulta SQL
    query = f'SELECT {columns} FROM {table_name}'
    if where_column and where_value is not None:
        query += f' WHERE {where_column} = ?'

    # Ejecutar la consulta SQL
    cursor.execute(query, (where_value,) if where_column and where_value is not None else ())

    # Obtener los resultados de la consulta
    resultados = cursor.fetchall()
    columnas = [descripcion[0] for descripcion in cursor.description]

    # Cerrar la conexión
    conn.close()

    return resultados, columnas

def agregar_latlong(table_name,conn):
    data = pd.read_sql_query("SELECT RUT, UTM_Easting, UTM_Northing, UTM_Zone_Number, UTM_Zone_Letter FROM personas",conn)
    data.insert(len(data.columns),"Latitud",value=None)
    data.insert(len(data.columns),"Longitud",value=None)
    for i in range(len(data)):
        latlong = utm_to_latlong(data.iloc[i]["UTM_Easting"],data.iloc[i]["UTM_Northing"],data.iloc[i]["UTM_Zone_Number"],data.iloc[i]["UTM_Zone_Letter"])
        data.at[i,"Latitud"] = latlong[0]
        data.at[i,"Longitud"] = latlong[1]
    data.to_sql(table_name,conn,if_exists="replace",index=False)

def agregar_df_a_sqlite(df, database_name, table_name):
    """
    Agrega un DataFrame a una tabla SQLite.

    Parámetros:
    df (pd.DataFrame): DataFrame a agregar a la base de datos.
    database_name (str): Nombre del archivo de la base de datos SQLite.
    table_name (str): Nombre de la tabla donde se insertará el DataFrame.
    """
    # Conectar a la base de datos SQLite
    conn = sqlite3.connect(database_name)
    
    # Agregar el DataFrame a la tabla SQLite
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    agregar_latlong("coordenadas",conn)
    drop_columns = ["UTM_Easting","UTM_Northing","UTM_Zone_Letter","UTM_Zone_Number"]
    if "Longitud" in list(df.columns):
        drop_columns.extend(["Latitud","Longitud"])
    df.drop(columns=drop_columns,inplace=True)
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    global datos
    datos, columnas = ejecutar_query_sqlite(database_name,"personas pe NATURAL JOIN coordenadas co")
    datos = pd.DataFrame(datos,columns=columnas)
    
    # Cerrar la conexión
    conn.close()
    global archivo
    archivo = archivo[:-4]+".sql"
    mostrar_datos(datos)
    mensaje_datos_gardados()

#documentacion=https://github.com/TomSchimansky/TkinterMapView?tab=readme-ov-file#create-path-from-position-list
def get_country_city(lat,long):
    country = tkintermapview.convert_coordinates_to_country(lat, long)
    print(country)
    city = tkintermapview.convert_coordinates_to_city(lat, long)
    return country,city
# Definir la función para convertir UTM a latitud y longitud
def utm_to_latlong(easting, northing, zone_number, zone_letter):
    # Crear el proyector UTM
    utm_proj = pyproj.Proj(proj='utm', zone=zone_number, datum='WGS84')
    
    # Convertir UTM a latitud y longitud
    longitude, latitude = utm_proj(easting, northing, inverse=True)
    return round(latitude,2), round(longitude,2)

def combo_event1(value):
    global archivo, marker_1
    result, columnas =ejecutar_query_sqlite(archivo, 'coordenadas NATURAL JOIN personas',columns='Latitud,Longitud,Nombre,Apellido', where_column='RUT', where_value=value)
    nombre_apellido=str(result[0][2])+' '+str(result[0][3])
    if not marker_1 == None:
        marker_1.delete()
    marker_1 = map_widget.set_marker(result[0][0], result[0][1], text=nombre_apellido)
    activar_rut2()

def combo_event2(value):
    global archivo, marker_2
    result, columnas =ejecutar_query_sqlite(archivo, 'coordenadas NATURAL JOIN personas',columns='Latitud,Longitud,Nombre,Apellido', where_column='RUT', where_value=value)
    nombre_apellido=str(result[0][2])+' '+str(result[0][3])
    if not marker_2 == None:
        marker_2.delete()
    marker_2 = map_widget.set_marker(result[0][0], result[0][1], text=nombre_apellido)
    activar_boton_calcular()

def activar_rut2():
    global optionmenu_2
    ruts = ejecutar_query_sqlite(archivo,"coordenadas","RUT")   # funcion devuelve values y columnas, indice 0 es values
    lista_ruts = []
    for rut in ruts[0]:                 # ruts[0] entrega una tupla de forma ("xxxxxxx-x",)
        lista_ruts.append(rut[0])       # se toma el primer elemento de esa tupla
    label_rut2.grid(row=0, column=2, padx=5, pady=5)
    optionmenu_2.configure(values=lista_ruts)
    optionmenu_2.set("Elige un RUT")
    optionmenu_2.grid(row=0, column=3, padx=5, pady=(5, 5))

def actualizar_frame3():
    ruts = ejecutar_query_sqlite(archivo,"coordenadas","RUT")
    lista_ruts = []
    for rut in ruts[0]:                 
        lista_ruts.append(rut[0])       
    optionmenu_1.configure(values=lista_ruts)
    optionmenu_1.set("Elige un RUT")
    optionmenu_2.set("Elige un RUT")
    optionmenu_2.grid_forget()
    label_rut2.grid_forget()
    boton_calcular.grid_forget()
    texto.grid_forget()
    map_widget.delete_all_path()

def activar_boton_calcular():
    boton_calcular.grid(row=0, column=4, padx=5, pady=(5, 5))
    
def combo_event(value):
    pass
    #mapas.set_address("moneda, santiago, chile")
    #mapas.set_position(48.860381, 2.338594)  # Paris, France
    #mapas.set_zoom(15)
    #address = tkintermapview.convert_address_to_coordinates("London")
    #print(address)
def center_window(window, width, height):
    # Obtener el tamaño de la ventana principal
    root.update_idletasks()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    root_x = root.winfo_x()
    root_y = root.winfo_y()

    # Calcular la posición para centrar la ventana secundaria
    x = root_x + (root_width // 2) - (width // 2)
    y = root_y + (root_height // 2) - (height // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")

def setup_toplevel(window):
    window.geometry("400x500")
    window.title("Modificar datos")
    center_window(window, 400, 500)  # Centrar la ventana secundaria
    window.lift()  # Levanta la ventana secundaria
    window.focus_force()  # Forzar el enfoque en la ventana secundaria
    window.grab_set()  # Evita la interacción con la ventana principal

    
def calcular_distancia(RUT1,RUT2):
    map_widget.delete_all_path()
    distancia = haversine(RUT1[0],RUT1[1],RUT2[0],RUT2[1])
    texto.configure(text=f"La distancia es de {distancia:.2f} Km.")
    texto.grid(row=1, column=1, padx=5, pady=(5, 5))
    linea = map_widget.set_path([marker_1.position,marker_2.position],color="#CF352E")

def guardar_data(row_selector):
    print(row_selector.get())
    #print(row_selector.table.values)
def editar_panel(root):
    global toplevel_window, rowselector, datos
    if rowselector.get():
        row_index = datos[datos["RUT"] == rowselector.get()[0][0]].index[0]
        if toplevel_window is None or not toplevel_window.winfo_exists():
            toplevel_window = ctk.CTkToplevel(root)
            setup_toplevel(toplevel_window)
            scrollable_top = ctk.CTkScrollableFrame(master=toplevel_window)
            scrollable_top.pack(fill="both",expand=True)

            row_columns = [rowselector.get()[0], list(datos.columns)]
            if "Longitud" in row_columns[1]:
                del row_columns[1][-2:]
            entradas = []

            for i in range(len(row_columns[1])):
                column_name = row_columns[1][i]
                label = ctk.CTkLabel(scrollable_top,text=column_name)
                label.pack()
                value = row_columns[0][i]
                i = ctk.CTkEntry(scrollable_top)
                i.insert(0,value)
                i.pack()
                entradas.append(i)
            
            boton_editar = ctk.CTkButton(scrollable_top,text="Guardar cambios",command= lambda:editar_fila(row_index,entradas))
            boton_editar.pack(pady=10)
        else:
            toplevel_window.focus()
    else:
        mensaje_seleccionar_fila()

def editar_fila(index,entradas):
    row = []
    for i in range(len(entradas)):
        nuevo_dato = entradas[i].get()
        row.append(nuevo_dato)
    global datos, archivo
    for i in range(len(entradas)):
        try:
            row[i] = int(row[i])
            datos.iloc[[index],[i]] = row[i]
        except ValueError:
            datos.iloc[[index],[i]] = row[i]
    if archivo[-4:] == ".sql":
        latlong = utm_to_latlong(datos.iloc[index]["UTM_Easting"],datos.iloc[index]["UTM_Northing"],datos.iloc[index]["UTM_Zone_Number"],datos.iloc[index]["UTM_Zone_Letter"])
        datos.iloc[[index],[-2]] = latlong[0]
        datos.iloc[[index],[-1]] = latlong[1]
    mostrar_datos(datos)
    toplevel_window.destroy()

def eliminar_fila():
    if rowselector.get():
        row_index = datos[datos["RUT"] == rowselector.get()[0][0]].index[0]
        mensaje_eliminar_fila(row_index)
    else:
        mensaje_seleccionar_fila()

# Función para manejar la selección del archivo
def seleccionar_archivo():
    archivo = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv"),("Archivos SQL", "*.sql")])
    if archivo[-4:] == ".csv":
        print(f"Archivo seleccionado: {archivo}")
        leer_archivo_csv(archivo) # antes: mostrar_datos(archivo)
    elif archivo[-4:] == ".sql":
        leer_archivo_sql(archivo)
def on_scrollbar_move(*args):
    canvas.yview(*args)
    canvas.bbox("all")
def leer_archivo_csv(ruta_archivo):
    global datos, archivo
    try:
        datos = pd.read_csv(ruta_archivo)
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
    else:
        archivo = ruta_archivo
        mostrar_datos(datos)

def leer_archivo_sql(ruta_archivo):
    global datos, archivo
    try:
        data,columns = ejecutar_query_sqlite(ruta_archivo,"personas NATURAL JOIN coordenadas")
        datos = pd.DataFrame(data,columns=columns)
    except Exception as e:
        print(f"Error al leer el archivo SQL: {e}")
    else:
        archivo = ruta_archivo
        print(f"Archivo seleccionado: {archivo}")
        mostrar_datos(datos)

def actualiza_combobox(datos):
    global combobox_left, combobox_right
    combobox_left.configure(values=sorted(list(set(datos["Pais"]))))
    combobox_left.set("Seleccione País")

    combobox_right.configure(values=sorted(list(set(datos["Profesion"]))))
    combobox_right.set("Seleccione Profesión")

def update_grafico1(choice):
    global datos, profesiones, x, y, fig1, ax1, canvas1
    data_pais = datos[datos["Pais"] == choice]

    ax1.clear()
    profesiones = sorted(list(set(data_pais["Profesion"])))
    x = np.arange(len(profesiones))
    y = []
    for profesion in profesiones:
        y.append(len(data_pais[data_pais["Profesion"] == profesion]))
    ax1.bar(x, y)
    ax1.set_xticks(x)
    ax1.set_xticklabels(profesiones)
    ax1.set_xlabel("Profesiones")
    ax1.set_ylabel("Numero de profesionales")
    ax1.set_title("Profesiones vs Paises")
    if canvas1: canvas1.get_tk_widget().pack_forget()
    canvas1 = FigureCanvasTkAgg(fig1, master=left_panel)
    canvas1.draw()
    canvas1.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

def update_grafico2(choice):
    global datos, profesiones, labels, sizes, colors, fig2, ax2, canvas2
    data_profesion = datos[datos["Profesion"] == choice]
    labels = sorted(list(set(data_profesion["Estado_Emocional"])))
    sizes = []
    for emocion in labels:
        sizes.append(len(data_profesion[data_profesion["Estado_Emocional"] == emocion]))
    colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
    ax2.clear()
    ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
    ax2.axis('equal')  # para que el gráfico sea un círculo
    ax2.set_title("Estado emocional vs profesion")
    if canvas2: canvas2.get_tk_widget().pack_forget()
    canvas2 = FigureCanvasTkAgg(fig2, master=right_panel)
    canvas2.draw()
    canvas2.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

# Función para mostrar los datos en la tabla
def mostrar_datos(datos:pd.DataFrame):
    global rowselector
    
    datos_mostrados = datos.to_dict("list")
    rows = len(list(datos_mostrados.values())[0])
    values = []
    for col in range(rows):
        values.append([])
    for i in range(rows):
        for key in datos_mostrados.keys():
            values[i].append(datos_mostrados[key][i])
        
    values.insert(0,list(datos_mostrados.keys()))

    for widget in scrollable_frame.winfo_children():
        widget.destroy()
    
    tabla = CTkTable(master=scrollable_frame,column=len(datos_mostrados.keys()),values=values,header_color="#79CAC1")
    tabla.pack(expand=True,fill="both")

    rowselector = CTkTableRowSelector(tabla)
    rowselector.max_selection = 1

    # Botón para imprimir las filas seleccionadas
    boton_imprimir = ctk.CTkButton(
        master=home_frame, text="guardar informacion", command=lambda: agregar_df_a_sqlite(datos,archivo[:-4]+".sql","personas"))
    boton_imprimir.grid(row=2, column=0, pady=(0, 20))
    
    # Botón para imprimir las filas seleccionadas
    boton_imprimir = ctk.CTkButton(
        master=data_panel_superior, text="modificar dato", command=lambda: editar_panel(root))
    boton_imprimir.grid(row=0, column=2, pady=(0, 0))

    # Botón para imprimir las filas seleccionadas
    boton_imprimir = ctk.CTkButton(
        master=data_panel_superior, text="Eliminar dato", command=eliminar_fila,fg_color='purple',hover_color='red')
    boton_imprimir.grid(row=0, column=3, padx=(10, 0))
def select_frame_by_name(name):
    home_button.configure(fg_color=("gray75", "gray25") if name == "home" else "transparent")
    frame_2_button.configure(fg_color=("gray75", "gray25") if name == "frame_2" else "transparent")
    frame_3_button.configure(fg_color=("gray75", "gray25") if name == "frame_3" else "transparent")

    if name == "home":
        home_frame.grid(row=0, column=1, sticky="nsew")
    else:
        home_frame.grid_forget()
    if name == "frame_2":
        second_frame.grid(row=0, column=1, sticky="nsew")
    else:
        second_frame.grid_forget()
    if name == "frame_3":
        third_frame.grid(row=0, column=1, sticky="nsew")
    else:
        third_frame.grid_forget()

def home_button_event():
    select_frame_by_name("home")
    if archivo[-4:] == ".sql":
        data,columns = ejecutar_query_sqlite(archivo,"personas NATURAL JOIN coordenadas")
        global datos
        datos = pd.DataFrame(data,columns=columns)
        mostrar_datos(datos)

def frame_2_button_event():
    if archivo[-4:] == ".sql":
        select_frame_by_name("frame_2")
        data,columns = ejecutar_query_sqlite(archivo,"personas")
        global datos
        datos = pd.DataFrame(data,columns=columns)
        actualiza_combobox(datos)
    else:
        mensaje_acceso_bloqueado()

def frame_3_button_event():
    if archivo[-4:] == ".sql":
        select_frame_by_name("frame_3")
        data,columns = ejecutar_query_sqlite(archivo,"coordenadas")
        global datos
        datos = pd.DataFrame(data,columns=columns)
        actualizar_frame3()
        if marker_1 is not None:
            marker_1.delete()
        if marker_2 is not None:
            marker_2.delete()
    else:
        mensaje_acceso_bloqueado()

def mensaje_acceso_bloqueado():
    msg = CTkMessagebox(title="Ventana no disponible",message="Para ingresar primero guarda la tabla de datos o carga un archivo .sql",icon="cancel")

def mensaje_datos_gardados():
    msg = CTkMessagebox(title="Guardado",message="Se ha actualizado la base de datos exitosamente",icon="check")

def mensaje_seleccionar_fila():
    msg = CTkMessagebox(title="Modificacion de tabla",message="Seleccione una fila primero",icon="warning")

def mensaje_eliminar_fila(index):
    msg = CTkMessagebox(title="Eliminar fila",message="Está seguro que quiere eliminar la fila seleccionada?",icon="warning",option_1="Eliminar",option_2="Cancelar")
    eleccion = msg.get()
    if eleccion == "Eliminar":
        global datos
        datos.drop([index],inplace=True)
        mostrar_datos(datos)
        msg.destroy()
    else:
        msg.destroy()

def change_appearance_mode_event(new_appearance_mode):
    ctk.set_appearance_mode(new_appearance_mode)
def mapas(panel):
    # create map widget
    map_widget = tkintermapview.TkinterMapView(panel,width=800, height=500, corner_radius=0)
    #map_widget.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
    map_widget.pack(fill=ctk.BOTH, expand=True)
    return map_widget
# Crear la ventana principal
root = ctk.CTk()
root.title("Proyecto Final progra I 2024")
root.geometry("950x450")

# Configurar el diseño de la ventana principal
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Establecer la carpeta donde están las imágenes
image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "iconos")
logo_image = ctk.CTkImage(Image.open(os.path.join(image_path, "uct.png")), size=(140, 50))
home_image = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "db.png")),
                          dark_image=Image.open(os.path.join(image_path, "home_light.png")), size=(20, 20))
chat_image = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "chat_dark.png")),
                          dark_image=Image.open(os.path.join(image_path, "chat_light.png")), size=(20, 20))
add_user_image = ctk.CTkImage(light_image=Image.open(os.path.join(image_path, "add_user_dark.png")),
                              dark_image=Image.open(os.path.join(image_path, "add_user_light.png")), size=(20, 20))

# Crear el marco de navegación
navigation_frame = ctk.CTkFrame(root, corner_radius=0)
navigation_frame.grid(row=0, column=0, sticky="nsew")
navigation_frame.grid_rowconfigure(4, weight=1)

navigation_frame_label = ctk.CTkLabel(navigation_frame, text="", image=logo_image,
                                      compound="left", font=ctk.CTkFont(size=15, weight="bold"))
navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

home_button = ctk.CTkButton(navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Home",
                            fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                            image=home_image, anchor="w", command=home_button_event)
home_button.grid(row=1, column=0, sticky="ew")

frame_2_button = ctk.CTkButton(navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Frame 2",
                               fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                               image=chat_image, anchor="w", command=frame_2_button_event)
frame_2_button.grid(row=2, column=0, sticky="ew")

frame_3_button = ctk.CTkButton(navigation_frame, corner_radius=0, height=40, border_spacing=10, text="Frame 3",
                               fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                               image=add_user_image, anchor="w", command=frame_3_button_event)
frame_3_button.grid(row=3, column=0, sticky="ew")

appearance_mode_menu = ctk.CTkOptionMenu(navigation_frame, values=["Light", "Dark", "System"],
                                         command=change_appearance_mode_event)
appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

# Crear el marco principal de inicio



# Crear el marco de navegación
home_frame = ctk.CTkFrame(root, fg_color="transparent")
home_frame.grid_rowconfigure(1, weight=1)
home_frame.grid_columnconfigure(0, weight=1)

data_panel_superior = ctk.CTkFrame(home_frame, corner_radius=0,)
data_panel_superior.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

data_panel_inferior = ctk.CTkFrame(home_frame, corner_radius=0)
data_panel_inferior.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
data_panel_inferior.grid_rowconfigure(0, weight=1)
data_panel_inferior.grid_columnconfigure(0, weight=1)

home_frame_large_image_label = ctk.CTkLabel(data_panel_superior, text="Ingresa el archivo en formato .csv o .sql",font=ctk.CTkFont(size=15, weight="bold"))
home_frame_large_image_label.grid(row=0, column=0, padx=15, pady=15)
home_frame_cargar_datos=ctk.CTkButton(data_panel_superior, command=seleccionar_archivo,text="Cargar Archivo",fg_color='green',hover_color='gray')
home_frame_cargar_datos.grid(row=0, column=1, padx=15, pady=15)

scrollable_frame = ctk.CTkScrollableFrame(master=data_panel_inferior)
scrollable_frame.grid(row=0, column=0,sticky="nsew")



# Crear el segundo marco
second_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
#second_frame.grid_rowconfigure(0, weight=1)
#second_frame.grid_columnconfigure(0, weight=1)
second_frame.grid_rowconfigure(1, weight=1)
second_frame.grid_columnconfigure(1, weight=1)

# Crear el frame superior para los comboboxes
top_frame = ctk.CTkFrame(second_frame)
top_frame.pack(side=ctk.TOP, fill=ctk.X)

# Crear el frame inferior para los dos gráficos
bottom_frame = ctk.CTkFrame(second_frame)
bottom_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

# Crear los paneles izquierdo y derecho para los gráficos
left_panel = ctk.CTkFrame(bottom_frame)
left_panel.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

right_panel = ctk.CTkFrame(bottom_frame)
right_panel.pack(side=ctk.RIGHT, fill=ctk.BOTH, expand=True)

# Crear los paneles superior izquierdo y derecho para los comboboxes
top_left_panel = ctk.CTkFrame(top_frame)
top_left_panel.pack(side=ctk.LEFT, fill=ctk.X, expand=True)

top_right_panel = ctk.CTkFrame(top_frame)
top_right_panel.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)


# Variable global con los datos y el nombre del archivo
datos = pd.DataFrame()
archivo = ""

rowselector = None

# Agregar un Combobox al panel superior izquierdo
combobox_left = ctk.CTkComboBox(top_left_panel, values=["Opción 1", "Opción 2", "Opción 3"],command=update_grafico1)
combobox_left.pack(pady=20, padx=20)

# Agregar un Combobox al panel superior derecho
combobox_right = ctk.CTkComboBox(top_right_panel, values=["Opción 1", "Opción 2", "Opción 3"],command=update_grafico2)
combobox_right.pack(pady=20, padx=20)
# Crear el gráfico de barras en el panel izquierdo
fig1, ax1 = plt.subplots()
profesiones = ["Profesion A", "Profesion B", "Profesion C", "Profesion D", "Profesion E"]
paises = ["País 1", "País 2", "País 3", "País 4", "País 5"]
x = np.arange(len(profesiones))
y = np.random.rand(len(profesiones))
ax1.bar(x, y)
ax1.set_xticks(x)
ax1.set_xticklabels(profesiones)
ax1.set_xlabel("Profesiones")
ax1.set_ylabel("Numero de profesionales")
ax1.set_title("Profesiones vs Paises")

# Integrar el gráfico en el panel izquierdo
canvas1 = FigureCanvasTkAgg(fig1, master=left_panel)
canvas1.draw()
canvas1.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

# Crear el gráfico de torta en el panel derecho
fig2, ax2 = plt.subplots()
labels = 'A', 'B', 'C', 'D'
sizes = [15, 30, 45, 10]
colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue']
explode = (0.1, 0, 0, 0)  # explotar la porción 1

ax2.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
ax2.axis('equal')  # para que el gráfico sea un círculo
ax2.set_title("Estado emocional vs profesion")

# Integrar el gráfico de torta en el panel derecho
canvas2 = FigureCanvasTkAgg(fig2, master=right_panel)
canvas2.draw()
canvas2.get_tk_widget().pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)


# Crear el tercer marco
third_frame = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
third_frame.grid_rowconfigure(0, weight=1)
third_frame.grid_columnconfigure(0, weight=1)
third_frame.grid_rowconfigure(1, weight=3)  # Panel inferior 3/4 más grande
# Crear dos bloques dentro del frame principal
third_frame_top =  ctk.CTkFrame(third_frame, fg_color="gray")
third_frame_top.grid(row=0, column=0,  sticky="nsew", padx=5, pady=5)

third_frame_inf =  ctk.CTkFrame(third_frame, fg_color="lightgreen")
third_frame_inf.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
map_widget=mapas(third_frame_inf)
label_rut = ctk.CTkLabel(third_frame_top, text="RUT",font=ctk.CTkFont(size=15, weight="bold"))
label_rut.grid(row=0, column=0, padx=5, pady=5)

label_rut2 = ctk.CTkLabel(third_frame_top, text="RUT",font=ctk.CTkFont(size=15, weight="bold"))

optionmenu_1 = ctk.CTkOptionMenu(third_frame_top, dynamic_resizing=True,
                                                        values=["Value 1", "Value 2", "Value Long Long Long"],command=lambda value:combo_event1(value))
optionmenu_1.grid(row=0, column=1, padx=5, pady=(5, 5))

optionmenu_2 = ctk.CTkOptionMenu(third_frame_top,dynamic_resizing=True,values=["blablabla"],command= lambda value:combo_event2(value))

boton_calcular = ctk.CTkButton(third_frame_top,text="Calcular distancia",command=lambda:calcular_distancia(marker_1.position,marker_2.position))

texto = ctk.CTkLabel(third_frame_top,text="blablalab")

marker_1 = None
marker_2 = None




# Seleccionar el marco predeterminado
select_frame_by_name("home")
toplevel_window = None
root.protocol("WM_DELETE_WINDOW", root.quit)
# Ejecutar el bucle principal de la interfaz
root.mainloop()
