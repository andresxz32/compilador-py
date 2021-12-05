# errors.py
#
# Soporte de manejo de errores del compilador.
#
# Una de las partes más importantes (y molestas) de escribir un compilador
# es la notificación confiable de los mensajes de error al usuario. Este
# archivo debería consolidar algunas funciones básicas de manejo de errores
# en un solo lugar. Facilite la notificación de errores. Facilite la
# búsqueda de errores.

# Podría expandir esto para que sea más poderoso más adelante

# Variable global que indica si se ha producido algún error. El compilador
# puede ver esto más tarde para decidir si morir o no.

_errors_detected = 0

class CompilerError(Exception):
	pass

def warning(message, lineno=None):
	global _errors_detected
	if lineno:
		print(f'{lineno}: {message}')
	else:
		print(message)
	_errors_detected += 1

def execerror(message, lineno=None):
	warning(message, lineno)
	#exit(1)

def errors_detected():
	return _errors_detected
	
def clear_errors():
	global _errors_detected
	_errors_detected = 0
