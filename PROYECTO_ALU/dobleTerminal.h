#ifndef dobleTerminal_h 
#define dobleTerminal_h
#include "terminal.h"

struct dobleTerminal{
	terminal* entrada=nullptr;
	terminal* sig1=nullptr;
	terminal* sig2=nullptr;
	bool signal=false;
	
	void conectarD1(terminal* t){
		entrada=t; signal=t->signalBef;
	}
	
	void conectarD2(terminal *t1,terminal *t2){
		sig1=t1; sig1->setSignal(signal);
		sig2=t2; sig2->setSignal(signal);
	}
	void propagar(){
		signal=entrada->signalBef;
		sig1->setSignal(signal);
		sig2->setSignal(signal);
	}
};

#endif
