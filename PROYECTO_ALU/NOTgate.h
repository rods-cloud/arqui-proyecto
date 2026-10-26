#ifndef NOTgate_h
#define NOTgate_h
#include "terminal.h"
#include "transistor.h"

class NOTgate{
	private:
		terminal* salida = new terminal();
	public:
		terminal* evNOT(transistor* t, terminal* vcc){
			// Pull-up hacia VCC
			vcc->conectarTerminales(t->getColector());
			t->setEmisorGND();
			t->actEmisor();
			t->getColector()->conectarTerminales(salida);
			return salida;
		}
		
		void revNOT(bool signal, transistor* t){
			t->getBase()->setSignal(signal);
			t->setEmisorGND();
			t->actEmisor();
			// El colector ya contiene la salida invertida
			salida->setSignal(t->getColector()->signalBef);
		}
};

#endif
