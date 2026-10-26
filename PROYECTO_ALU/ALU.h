#ifndef ALU_h
#define ALU_h
#include "terminal.h"
#include "dobleTerminal.h"
#include "transistor.h"
#include "ANDgate.h"
#include "ORgate.h"
#include "NOTgate.h"
#include "XORgate.h"
#include "inversor.h"

class ALU{
	private:
		terminal* salida[8];
	public:
		void ALU_suma(terminal* suma, terminal* c[], terminal* aux[], terminal* r1, terminal* r2, transistor* NOT[], transistor* AND[], transistor* OR[], terminal* XORter[], terminal* vcc[], dobleTerminal* dobTer[], ANDgate ANDg[], NOTgate NOTg[], ORgate ORg[], XORgate XORg[], transistor* NOTx[], transistor* ANDx[], transistor* ORx[], terminal* XORxter[], terminal* vccx[], dobleTerminal* dobTerx[], ANDgate ANDgx[], NOTgate NOTgx[], ORgate ORgx){
			r1->conectarTerminales(XORter[0]);
			r2->conectarTerminales(XORter[1]);
			//XORter[0-5]
			//NOTg[0-1], ANDg[0-1], ORg[0]
			//vcc[0-5]
			//NOT[0-1]
			//AND[0-3]
			//OR[0-1]
			//XORg[0]
			
			XORg[0].evXOR(NOT, AND, OR, XORter, vcc, dobTer, ANDg, NOTg, ORg[0])->conectarTerminales(aux[0]);
			//aux[0]->XOR(r1,r2)			
			
			aux[1]->setSignal(aux[0]->signalBef);
			//aux[1]->XOR(r1,r2)			
			
			AND[4]->getBase()->setSignal(r1->signalBef);
			AND[5]->getBase()->setSignal(r2->signalBef);
			//AND[4]:Base->r1, AND[5]:Base->r2
			
			ANDg[2].evAND(AND[4], AND[5], vcc[6])->conectarTerminales(OR[2]->getBase());
			//OR[2]:Base->AND(r1,r2)
			
			AND[6]->getBase()->setSignal(aux[0]->signalBef);
			AND[7]->getBase()->setSignal(c[0]->signalBef);
			//AND[6]:Base->XOR(r1,r2), AND[7]:Base->cin=c[0]
			
			ANDg[3].evAND(AND[6], AND[7], vcc[7])->conectarTerminales(OR[3]->getBase());
			//OR[3]:Base->AND(cin,XOR(r1,r2))
			
			ORg[1].evOR(OR[2], OR[3], vcc[8], vcc[9])->conectarTerminales(c[1]);
			//c[1]:=cout->OR(AND(r1,r2), AND(cin, XOR(r1,r2)))
			
			aux[1]->conectarTerminales(XORxter[0]);
			c[0]->conectarTerminales(XORxter[1]);
			XORg[1].evXOR(NOTx, ANDx, ORx, XORxter, vccx, dobTerx, ANDgx, NOTgx, ORgx)->conectarTerminales(aux[2]);
			//aux2->XOR(XOR(r1,r2), cin)
			aux[2]->conectarTerminales(suma);
		}
		void restablecer(terminal* c[], terminal* suma, terminal* aux[]){
			c[0]->setSignal(false);
			c[1]->setSignal(false);
			suma->setSignal(false);
			aux[0]->setSignal(false);
			aux[1]->setSignal(false);
			aux[2]->setSignal(false);
		}
		
		void revSuma(terminal* suma, terminal* c[], terminal* aux[], terminal* r1, terminal* r2, transistor* NOT[], transistor* AND[], transistor* OR[], terminal* XORter[], terminal* vcc[], dobleTerminal* dobTer[], ANDgate ANDg[], NOTgate NOTg[], ORgate ORg[], XORgate XORg[], transistor* NOTx[], transistor* ANDx[], transistor* ORx[], terminal* XORxter[], terminal* vccx[], dobleTerminal* dobTerx[], ANDgate ANDgx[], NOTgate NOTgx[], ORgate ORgx){
			XORter[0]->setSignal(r1->signalBef);
			XORter[1]->setSignal(r2->signalBef);
			
			
			aux[0]->setSignal(XORg[0].evXOR(NOT, AND, OR, XORter, vcc, dobTer, ANDg, NOTg, ORg[0])->signalBef);
			aux[1]->setSignal(aux[0]->signalBef);
			
			AND[4]->getBase()->setSignal(r1->signalBef);
			AND[5]->getBase()->setSignal(r2->signalBef);
			
			OR[2]->getBase()->setSignal(ANDg[2].evAND(AND[4], AND[5], vcc[6])->signalBef);
			AND[6]->getBase()->setSignal(aux[0]->signalBef);
			AND[7]->getBase()->setSignal(c[0]->signalBef);
			
			OR[3]->getBase()->setSignal(ANDg[3].evAND(AND[6], AND[7], vcc[7])->signalBef);
			c[1]->setSignal(ORg[1].evOR(OR[2], OR[3], vcc[8], vcc[9])->signalBef);
			
			XORxter[0]->setSignal(aux[1]->signalBef);
			XORxter[1]->setSignal(c[0]->signalBef);
			aux[2]->setSignal(XORg[1].evXOR(NOTx, ANDx, ORx, XORxter, vccx, dobTerx, ANDgx, NOTgx, ORgx)->signalBef);
			
			suma->setSignal(aux[2]->signalBef);
		}
	
		void ALU_desplazarM(terminal* Q[], terminal* A[], terminal *c){
			for(int i=0;i<7;i++){
				Q[i]->setSignal(Q[i+1]->signalBef);
			} Q[7]->setSignal(A[0]->signalBef);
			
			for(int i=0;i<7;i++){
				A[i]->setSignal(A[i+1]->signalBef);
			} A[7]->setSignal(c->signalBef);
			c->setSignal(false);
		}
		
		void ALU_multiplicar(terminal* M[], terminal* Q[], terminal* A[], terminal* mult[],terminal* Cout, terminal* suma[], terminal* c[][2], terminal* aux[][3], transistor* NOT[][2], transistor* AND[][8], transistor* OR[][4], terminal* XORter[][6], terminal* vcc[][10], dobleTerminal* dobTer[][2], ANDgate ANDg[][4], NOTgate NOTg[][2], ORgate ORg[][2], XORgate XORg[][2], transistor* NOTx[][2], transistor* ANDx[][4], transistor* ORx[][2], terminal* XORxter[][6], terminal* vccx[][6], dobleTerminal* dobTerx[][2], ANDgate ANDgx[][2], NOTgate NOTgx[][2], ORgate ORgx[]){
		    
			for(int i=0; i<8; i++){A[i]->setSignal(false);}		
		    
			Cout->setSignal(false);
		    
			for(int i=0; i<16; i++){mult[i]->setSignal(false);}
		
		    for(int N=8; N>0; N--){
		        if(Q[0]->signalBef){
		            for(int i=0; i<8; i++){restablecer(c[i], suma[i], aux[i]);}
		            c[0][0]->setSignal(false);
		            for(int i=0; i<8; i++){
		                revSuma(suma[i], c[i], aux[i], A[i], M[i], NOT[i], AND[i], OR[i], XORter[i], vcc[i], dobTer[i], ANDg[i], NOTg[i], ORg[i], XORg[i], NOTx[i], ANDx[i], ORx[i], XORxter[i], vccx[i], dobTerx[i], ANDgx[i], NOTgx[i], ORgx[i]);
		                if(i<7){c[i+1][0]->setSignal(c[i][1]->signalBef);}
		            }
		            for(int i=0; i<8; i++){A[i]->setSignal(suma[i]->signalBef);}
		            Cout->setSignal(c[7][1]->signalBef);
		        }
		        else{Cout->setSignal(false);}
		        ALU_desplazarM(Q, A, Cout);
		    }
		    for(int i=0; i<8; i++){
		        mult[i]->setSignal(Q[i]->signalBef);
		        mult[i+8]->setSignal(A[i]->signalBef);
		    }
		}
		
		void ALU_desplazarD(terminal* Q[], terminal* A[]){
			for(int i=7;i>0;i--){
				A[i]->setSignal(A[i-1]->signalBef);
			} A[0]->setSignal(Q[7]->signalBef);
			for(int i=7;i>0;i--){
				Q[i]->setSignal(Q[i-1]->signalBef);
			} Q[0]->setSignal(false);
		}
		
		void ALU_division(terminal* M[], terminal* Q[], terminal* A[], terminal* Cout, terminal* suma[], terminal* c[][2], terminal* aux[][3], transistor* NOT[][2], transistor* AND[][8], transistor* OR[][4], terminal* XORter[][6], terminal* vcc[][10], dobleTerminal* dobTer[][2], ANDgate ANDg[][4], NOTgate NOTg[][2], ORgate ORg[][2], XORgate XORg[][2], transistor* NOTx[][2], transistor* ANDx[][4], transistor* ORx[][2], terminal* XORxter[][6], terminal* vccx[][6], dobleTerminal* dobTerx[][2], ANDgate ANDgx[][2], NOTgate NOTgx[][2], ORgate ORgx[], inversor INV, terminal* vcci[], transistor* NOTi[], NOTgate NOTgi[]){
			for(int i=0; i<8; i++){A[i]->setSignal(false);}		
			Cout->setSignal(false);
			
			terminal* aux1[8]; for(int i=0;i<8;i++) aux1[i]=new terminal();
			terminal* aux2[8]; for(int i=0;i<8;i++) aux2[i]=new terminal();
			for(int N=8; N>0; N--){
				ALU_desplazarD(Q,A);
				for(int i=0;i<8;i++) aux1[i]->setSignal(A[i]->signalBef);
				for(int i=0;i<8;i++) aux2[i]->setSignal(M[i]->signalBef);
				INV.invertirR2(1, aux2, vcci, NOTi, NOTgi, c[0][0]);
				
				for(int i=0; i<8; i++){
		            revSuma(suma[i], c[i], aux[i], aux1[i], aux2[i], NOT[i], AND[i], OR[i], XORter[i], vcc[i], dobTer[i], ANDg[i], NOTg[i], ORg[i], XORg[i], NOTx[i], ANDx[i], ORx[i], XORxter[i], vccx[i], dobTerx[i], ANDgx[i], NOTgx[i], ORgx[i]);
		            if(i<7){c[i+1][0]->setSignal(c[i][1]->signalBef);}
		        }
		        if (suma[7]->signalBef==false) {
		        	Q[0]->setSignal(true);
		        	for(int i=0;i<8;i++){
		        		A[i]->setSignal(suma[i]->signalBef);
					}
				}
		        else {
		        	Q[0]->setSignal(false);
				}				
		    }
		}
};
#endif
