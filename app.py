from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql

app = Flask(__name__)

db = pymysql.connect(
    host='os.getenv('DB_HOST')',
    user='os.getenv('DB_USER')',
    password='os.getenv('DB_PASSWORD')',
    database='os.getenv('DB_NAME')',
    port='os.getenv('DB_PORT')'
    cursorclass=pymysql.cursors.DictCursor
)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['usuario']
        password = request.form['password']
        cursor = db.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        if user and user['password'] == password:
            session['loggedin'] = True
            session['username'] = user['usuario']
            session['user_name'] = f"{user['nombre']} {user['apellido']}"
            return redirect(url_for('operaciones'))
          
        else:
            return 'Login fallido. Por favor, verifica tu usuario y contraseña.'
    return render_template('login.html')

@app.route('/realizarRetiros.html')
def loginRetiros():
    if 'loggedin' in session:
        user_name = session['user_name']
        return render_template('realizarRetiros.html', user_name=user_name)
    return redirect(url_for('login'))

@app.route('/realizarDeposito.html')
def loginDeposito():
    if 'loggedin' in session:
        user_name = session['user_name']
        return render_template('realizarDeposito.html', user_name=user_name)
    return redirect(url_for('login'))

@app.route('/analisis.html')
def loginStatus():
    if 'loggedin' in session:
        user_name = session['user_name']
        return render_template('analisis.html', user_name=user_name)
    return redirect(url_for('login'))

@app.route('/realizarTransferencias.html')
def loginTransf():
    if 'loggedin' in session:
        user_name = session['user_name']
        username = session['username']
        cursor = db.cursor()
        cursor.execute("SELECT numcuenta FROM cuentas WHERE cedula = (SELECT cedula FROM usuarios WHERE usuario = %s)", (username,))
        cuentas = cursor.fetchall()
        cursor.close()
        return render_template('realizarTransferencias.html', user_name=user_name, cuentas=cuentas)
    return redirect(url_for('login'))



@app.route('/operaciones.html')
def operaciones():
    if 'loggedin' in session:
        user_name = session['user_name']
        return render_template('operaciones.html', user_name=user_name)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/realizarRetiros.html')
def realizar_retiros():
    return render_template('realizarRetiros.html')

@app.route('/realizarDeposito.html')
def realizar_depositos():
    return render_template('realizarDeposito.html')

@app.route('/operaciones.html')
def realizar_op():
    return render_template('operaciones.html')

@app.route('/realizarTransferencias.html')
def realizar_tr():
    return render_template('realizarTransferencias.html')

@app.route('/analisis.html')
def realizar_analisis():
    return render_template('analisis.html')

@app.route('/obtener_cuentas', methods=['POST'])
def obtener_cuentas():
    cedula = request.form['cedula']
    cursor = db.cursor()
    cursor.execute("SELECT numcuenta FROM cuentas WHERE cedula = %s", (cedula,))
    cuentas = cursor.fetchall()
    cursor.close()
    return jsonify(cuentas)


@app.route('/procesar_retiro', methods=['POST'])
def procesar_retiro():
    if 'loggedin' in session:
        
        cedula = request.form['cedula']
        numcuenta = request.form['numcuenta']
        monto = float(request.form['monto'])
        fecha = request.form['fecha']

      
        cursor = db.cursor()
        cursor.execute("SELECT saldo FROM cuentas WHERE cedula = %s AND numcuenta = %s", (cedula, numcuenta))
        cuenta = cursor.fetchone()
        
        if not cuenta:
            return jsonify({'status': 'error', 'message': 'Cuenta no encontrada.'}), 400

        saldo_actual = cuenta['saldo']
        
        if saldo_actual < monto:
            return jsonify({'status': 'error', 'message': 'Fondos insuficientes.'}), 400

      
        nuevo_saldo = saldo_actual - monto
        cursor.execute("UPDATE cuentas SET saldo = %s WHERE cedula = %s AND numcuenta = %s", (nuevo_saldo, cedula, numcuenta))
        db.commit()
        cursor.close()

       
        mensaje = f'Retiro exitoso. Saldo actual: {nuevo_saldo}'

       
        return jsonify({'status': 'success', 'message': mensaje}), 200


    return jsonify({'status': 'error', 'message': 'Usuario no logeado.'}), 401

@app.route('/procesar_deposito', methods=['POST'])
def procesar_deposito():
    if 'loggedin' in session:
        cedula_beneficiario = request.form['cedula_beneficiario']
        numcuenta = request.form['numcuenta']
        monto = float(request.form['monto'])

        cursor = db.cursor()
        cursor.execute("SELECT saldo FROM cuentas WHERE cedula = %s AND numcuenta = %s", (cedula_beneficiario, numcuenta))
        cuenta = cursor.fetchone()
        
        if not cuenta:
            return jsonify({'status': 'error', 'message': 'Cuenta no encontrada.'}), 400

        saldo_actual = cuenta['saldo']
        nuevo_saldo = saldo_actual + monto
        cursor.execute("UPDATE cuentas SET saldo = %s WHERE cedula = %s AND numcuenta = %s", (nuevo_saldo, cedula_beneficiario, numcuenta))
        db.commit()
        cursor.close()

        mensaje = f'Depósito realizado con éxito. Saldo actual: {nuevo_saldo}'

        return jsonify({'status': 'success', 'message': mensaje}), 200

    return jsonify({'status': 'error', 'message': 'Usuario no logeado.'}), 401

if __name__ == '__main__':
    app.secret_key = 'supersecretkey'
    app.run(debug=True, port=5500)
