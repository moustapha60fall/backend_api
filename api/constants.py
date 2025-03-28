# constants.py

class CRUD:
	CREATE = 'new'
	READ = 'get'
	UPDATE = 'edit'
	DELETE = 'delete'
	# READ_AFTER_UPDATED = 'get-after-edit'

class ServerResponses:
	ADD_SUCCESS = 'Ajout enregistré.'
	UPDATE_SUCCESS = 'Modification enregistrée.'
	DELETE_SUCCESS = 'Suppression enregistrée.'
	OPERATION_FAILURE = "Échec de l'opération."
	
	@classmethod
	def getErrorMessage(cls, errorCode):
		# return '#' + str(errorCode) + ': ' + ServerResponses.OPERATION_FAILURE
		return ServerResponses.OPERATION_FAILURE + " (code d'erreur #" + str(errorCode) + ')'

