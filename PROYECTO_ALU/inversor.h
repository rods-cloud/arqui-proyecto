#ifndef inversor_h
#define inversor_h
#include "terminal.h"
#include "transistor.h"
#include "NOTgate.h"
class inversor{
	public:
		void invertirR2(int op, terminal* r2[], terminal* vcc[], transistor* NOT[], NOTgate NOTg[], terminal* cin){
			
			if(op==1){
				for(int i=0;i<8;i++){
					cin->setSignal(true);
					NOT[i]->getBase()->setSignal(r2[i]->signalBef);
					r2[i]->setSignal(NOTg[i].evNOT(NOT[i],vcc[i])->signalBef);
				}
			} else cin->setSignal(false);
		}
};




#endif
