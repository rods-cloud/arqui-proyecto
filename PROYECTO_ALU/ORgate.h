#ifndef ORgate_h
#define ORgate_h
#include "terminal.h"
#include "transistor.h"
#include "NOTgate.h"

class ORgate{
	private:
		terminal* salidaNor = new terminal();
		terminal* salida    = new terminal();
		transistor* tNot    = new transistor();
		NOTgate     ng;
	public:
		terminal* evOR(transistor* t1, transistor* t2, terminal *vcc1, terminal *vcc2){
			(void)vcc1; (void)vcc2;
			t1->setEmisorGND();
			t2->setEmisorGND();
			tNot->setEmisorGND();
			
			// Pull-up común para NOR
			salidaNor->setSignal(true);
			
			// NOR en PARALELO
			t1->tirarNodo(salidaNor);
			t2->tirarNodo(salidaNor);
			
			// NOR -> NOT para obtener OR
			salidaNor->conectarTerminales(tNot->getBase());
			tNot->setEmisorGND();
			tNot->actEmisor();
			tNot->getColector()->conectarTerminales(salida);
			return salida;
		}
		
		void revOR(bool signal1, bool signal2, transistor* t1, transistor* t2){
			t1->setEmisorGND();
			t2->setEmisorGND();
			tNot->setEmisorGND();
			
			salidaNor->setSignal(true);
			
			t1->getBase()->setSignal(signal1);
			t2->getBase()->setSignal(signal2);
			
			t1->tirarNodo(salidaNor);
			t2->tirarNodo(salidaNor);
			
			ng.revNOT(salidaNor->signalBef, tNot);
			salida->setSignal(tNot->getColector()->signalBef);
		}
};

#endif
