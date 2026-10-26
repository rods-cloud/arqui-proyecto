#ifndef XORgate_h
#define XORgate_h
#include "terminal.h"
#include "transistor.h"
#include "ANDgate.h"
#include "ORgate.h"
#include "NOTgate.h"
#include "dobleTerminal.h"

class XORgate{
	private:
		terminal* salida=new terminal();
	public:
		terminal* evXOR(transistor* NOT[], transistor* AND[], transistor* OR[], terminal* XORter[], terminal* vcc[], dobleTerminal* dobTer[], ANDgate ANDg[], NOTgate NOTg[], ORgate ORg){
			dobTer[0]->conectarD1(XORter[0]);
			dobTer[1]->conectarD1(XORter[1]);
			
			dobTer[0]->conectarD2(XORter[2], XORter[3]);
			dobTer[1]->conectarD2(XORter[4], XORter[5]);
			
			//XORter[2]->A
			//XORter[3]->A
			//XORter[4]->B
			//XORter[5]->B
			
			XORter[2]->conectarTerminales(NOT[0]->getBase());
			NOTg[0].evNOT(NOT[0], vcc[0])->conectarTerminales(AND[0]->getBase());
			XORter[5]->conectarTerminales(AND[1]->getBase());
			
			//AND[0]:Base->-A
			//AND[1]:Base->B
			
			XORter[4]->conectarTerminales(NOT[1]->getBase());
			NOTg[1].evNOT(NOT[1], vcc[1])->conectarTerminales(AND[2]->getBase());
			XORter[3]->conectarTerminales(AND[3]->getBase());
			
			//AND[2]:Base->-B
			//AND[3]:Base->A
			
			ANDg[0].evAND(AND[0],AND[1],vcc[2])->conectarTerminales(OR[0]->getBase());
			ANDg[1].evAND(AND[2],AND[3],vcc[3])->conectarTerminales(OR[1]->getBase());
			
			//OR[0]:Base->(-A) AND B
			//OR[1]:Base->(-B) AND A
			
			salida=ORg.evOR(OR[0], OR[1], vcc[4], vcc[5]);
			
			//salida: OR(AND(-A, B), AND(-B, A)
			
			return salida;
		}
		
		void revXOR(bool signal1, bool signal2, transistor* NOT[], transistor* AND[], transistor* OR[], terminal* XORter[], terminal* vcc[], dobleTerminal* dobTer[], ANDgate ANDg[], NOTgate NOTg[], ORgate ORg){
			XORter[0]->setSignal(signal1);
			dobTer[0]->propagar();
			
			XORter[1]->setSignal(signal2);
			dobTer[1]->propagar();

			NOT[0]->getBase()->setSignal(XORter[2]->signalBef);
			
			AND[0]->getBase()->setSignal(NOTg[0].evNOT(NOT[0], vcc[0])->signalBef);
			AND[1]->getBase()->setSignal(XORter[5]->signalBef);
			
			NOT[1]->getBase()->setSignal(XORter[4]->signalBef);
			
			AND[2]->getBase()->setSignal(NOTg[1].evNOT(NOT[1], vcc[1])->signalBef);
			AND[3]->getBase()->setSignal(XORter[3]->signalBef);
			
			OR[0]->getBase()->setSignal(ANDg[0].evAND(AND[0],AND[1],vcc[2])->signalBef);
			
			OR[1]->getBase()->setSignal(ANDg[1].evAND(AND[2],AND[3],vcc[3])->signalBef);
			
			salida->setSignal(ORg.evOR(OR[0], OR[1], vcc[4], vcc[5])->signalBef);
		}
};

#endif
