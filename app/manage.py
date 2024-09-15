def deploy():
	from app import create_app, db
	from flask_migrate import upgrade, migrate, stamp
	from models import (Users, Months, Facilities, TargetIndicator, SectionsTargetIndicator,
					 	ActionPlanImplementation, LevelImplementation5S,
						Workshops, TRMImplementation, CompanyTRMImplementation, SMEDImplementation,
						CompanySMEDImplementation, SOKImplementation, CompanySOKImplementation,
						ConductingTraining, CompanyConductingTraining, KaizenActivities, RegulationsAdaptation,
						CompanyRegulationsAdaptation, KPSCCompilation, SVMImplementation, CompanySVMImplementation,
						ExperienceExchange, CompanyExperienceExchange, PSZ)

	
	app = create_app()
	app.app_context().push()
	db.create_all()

	stamp()
	migrate()
	upgrade()

	return app

if __name__ == '__main__':
	import warnings
	warnings.simplefilter(action='ignore', category=FutureWarning)
	from gevent.pywsgi import WSGIServer
	app = deploy()
	server = WSGIServer(('localhost', 5000), app)
	server.serve_forever()