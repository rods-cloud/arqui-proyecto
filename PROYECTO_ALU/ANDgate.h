#ifndef ANDgate_h
#define ANDgate_h
#include "terminal.h"
#include "transistor.h"
#include "NOTgate.h"

class ANDgate{
	private:
		terminal* salidaNand = new terminal();
		terminal* salida     = new terminal();
		transistor* tNot     = new transistor();
		NOTgate     ng;
	public:
		terminal* evAND(transistor* t1, transistor* t2, terminal* vcc){
			(void)vcc;
			t1->setEmisorGND();
			t2->setEmisorGND();
			tNot->setEmisorGND();
			
			// Pull-up común para NAND
			salidaNand->setSignal(true);
			
			// NAND en SERIE: salidaNand -> t1.colector -> t1.emisor <- t2.colector <- t2.emisor -> GND
			t2->setEmisorGND();
			t2->actEmisor();
			t2->getColector()->conectarTerminales(t1->getEmisor());
			t1->actEmisor();
			t1->getColector()->conectarTerminales(salidaNand);
			
			// NAND -> NOT para obtener AND
			salidaNand->conectarTerminales(tNot->getBase());
			tNot->setEmisorGND();
			tNot->actEmisor();
			tNot->getColector()->conectarTerminales(salida);
			return salida;
		}
		
		void revAND(bool signal1, bool signal2, transistor* t1, transistor* t2){
			t1->setEmisorGND();
			t2->setEmisorGND();
			tNot->setEmisorGND();
			
			salidaNand->setSignal(true);
			
			t1->getBase()->setSignal(signal1);
			t2->getBase()->setSignal(signal2);
			
			t2->setEmisorGND();
			t2->actEmisor();
			t2->getColector()->conectarTerminales(t1->getEmisor());
			t1->actEmisor();
			t1->getColector()->conectarTerminales(salidaNand);
			
			ng.revNOT(salidaNand->signalBef, tNot);
			salida->setSignal(tNot->getColector()->signalBef);
		}
};

#endif
