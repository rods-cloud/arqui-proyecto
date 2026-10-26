#ifndef transistor_h
#define transistor_h
#include "terminal.h"

class transistor{
	private:
		terminal* colector;
		terminal* base;
		terminal* emisor;
	public:
		transistor(){
			colector = new terminal();
			base     = new terminal();
			emisor   = new terminal();
			// Emisor a masa por defecto (RTL)
			emisor->setSignal(false);
		}
		~transistor(){
			delete colector;
			delete base;
			delete emisor;
		}
		
		terminal* getColector(){ return colector; }
		terminal* getBase()    { return base; }
		terminal* getEmisor()  { return emisor; }
		
		void setEmisorGND(){
			emisor->setSignal(false);
		}
		
		// RTL NPN: si base==true conduce y el colector toma el nivel del emisor
		// si base==false queda en corte -> colector en VCC por pull-up lógico
		void actEmisor(){
			if(base->signalBef == true){
				colector->setSignal(emisor->signalBef);
			}else{
				colector->setSignal(true);
			}
		}
		
		// Para nodos compartidos (NOR en paralelo): solo puede bajar el nodo a GND
		void tirarNodo(terminal* nodo){
			if(base->signalBef == true && emisor->signalBef == false){
				nodo->setSignal(false);
			}
		}
};

#endif
