#include <iostream>
#include "terminal.h"
#include "dobleTerminal.h"
#include "transistor.h"
#include "ANDgate.h"
#include "ORgate.h"
#include "NOTgate.h"
#include "XORgate.h"
#include "ALU.h"
#include "inversor.h"

using namespace std;
int main(){
	int r1I; int r2I;
	string r1S; string r2S, VAr1, VAr2;
	bool r1B=false, r2B=false;
	int op=0;
	
	cout<<"Ingrese el registro 1: "; cin>>r1I;
	cout<<"Ingrese el registro 2: "; cin>>r2I;
	
	if(r1I<0) r1B=true;
	if(r2I<0) r2B=true;
	
	for(int i=0;i<8;i++){
		if(r1I%2==0) r1S="0"+r1S;
		else r1S="1"+r1S;
		
		if(r2I%2==0) r2S="0"+r2S;
		else r2S="1"+r2S;
		
		r1I=r1I/2;
		r2I=r2I/2;
	}
	
    VAr1=r1S; VAr2=r2S;
    
	if(r1B){
		
		for(int i=0;i<8;i++){
			if(r1S[i]=='0') r1S[i]='1';
			else {r1S[i]='0';}
		}
	}
	
	if(r2B){
		for(int i=0;i<8;i++){
			if(r2S[i]=='0') r2S[i]='1';
			else {r2S[i]='0';}
		}
	}
	
	if (r1B) {
	    for (int i = 7; i >= 0; i--) {
	        if (r1S[i] == '0') {r1S[i] = '1'; break;} 
			else {r1S[i] = '0';}
	    }
	}
	
	if (r2B) {
	    for (int i = 7; i >= 0; i--) {
	        if (r2S[i] == '0') {r2S[i] = '1'; break;} 
			else {r2S[i] = '0';}
	    }
	}
	
	cout<<"Ingrese el codigo de operacion: ";
	cin>>op;
	
	terminal* r1[8];  for(int i=0;i<8;i++){r1[i]=new terminal();}
	terminal* r2[8];  for(int i=0;i<8;i++){r2[i]=new terminal();} 
	
	//---------------------------------------------------------
	//Ingresan los elementos para suma o resta
	if(op==0||op==1){
		for(int i=0;i<8;i++){
			if(r1S[i]=='1'){r1[7-i]->setSignal(true);} 
			else {r1[7-i]->setSignal(false);}
		}
		for(int i=0;i<8;i++){
			if(r2S[i]=='1'){r2[7-i]->setSignal(true);} 
			else {r2[7-i]->setSignal(false);}
		}
	}
	
	//------------------------------------------------------------------------
	//Declaracion de los elementos del Full Adder:
	terminal* suma[8]; for(int i=0;i<8;i++){suma[i]=new terminal();}
	terminal* c[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){c[i][j]=new terminal();}} 
	terminal* aux[8][3]; for(int i=0;i<8;i++){for(int j=0;j<3;j++){aux[i][j]=new terminal();}}
	transistor* NOT[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){NOT[i][j]=new transistor();}}
	transistor* AND[8][8]; for(int i=0;i<8;i++){for(int j=0;j<8;j++){AND[i][j]=new transistor();}}
	transistor* OR[8][4]; for(int i=0;i<8;i++){for(int j=0;j<4;j++){OR[i][j]=new transistor();}}
	terminal* XORter[8][6]; for(int i=0;i<8;i++){for(int j=0;j<6;j++){XORter[i][j]=new terminal();}}
	terminal* vcc[8][10]; for(int i=0;i<8;i++){for(int j=0;j<10;j++){vcc[i][j]=new terminal(); vcc[i][j]->setSignal(true);}}
	dobleTerminal* dobTer[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){dobTer[i][j]=new dobleTerminal();}}
	ANDgate ANDg[8][4]; NOTgate NOTg[8][2]; ORgate ORg[8][2]; XORgate XORg[8][2]; 
	transistor* NOTx[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){NOTx[i][j]=new transistor();}}
	transistor* ANDx[8][4]; for(int i=0;i<8;i++){for(int j=0;j<4;j++){ANDx[i][j]=new transistor();}}
	transistor* ORx[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){ORx[i][j]=new transistor();}}
	terminal* XORxter[8][6]; for(int i=0;i<8;i++){for(int j=0;j<6;j++){XORxter[i][j]=new terminal();}}
	terminal* vccx[8][6]; for(int i=0;i<8;i++){for(int j=0;j<6;j++){vccx[i][j]=new terminal(); vccx[i][j]->setSignal(true);}}
	dobleTerminal* dobTerx[8][2]; for(int i=0;i<8;i++){for(int j=0;j<2;j++){dobTerx[i][j]=new dobleTerminal();}} 
	ANDgate ANDgx[8][2]; NOTgate NOTgx[8][2]; ORgate ORgx[8];
	ALU ALUs[8];
	
	//----------------------------------------------
	//Declaración de los elementos para el inversor
	
	terminal* vcci[8]; for(int i=0;i<8;i++){vcci[i]=new terminal(); vcci[i]->setSignal(true);}
	transistor* NOTi[8]; for(int i=0;i<8;i++){NOTi[i]=new transistor();}
	NOTgate NOTgi[8];
	
	inversor INV;
	INV.invertirR2(op, r2, vcci, NOTi, NOTgi, c[0][0]);
	
	//-----------------------------------------------
	//Operacion de suma
	for(int i=0;i<8;i++){
		ALUs[i].ALU_suma(suma[i], c[i], aux[i], r1[i], r2[i], NOT[i], AND[i], OR[i], XORter[i], vcc[i], dobTer[i], ANDg[i], NOTg[i], ORg[i], XORg[i], NOTx[i], ANDx[i], ORx[i], XORxter[i], vccx[i], dobTerx[i], ANDgx[i], NOTgx[i], ORgx[i]);
		if(i<7) c[i+1][0]->setSignal(c[i][1]->signalBef);
	}
	
	if(op==0||op==1){
		cout<<endl<<"----------------------------------"<<endl<<"Resultado: ";
		for(int i=7;i>=0;i--){
			if(suma[i]->signalBef){cout<<"1";} 
			else {cout<<"0";}
		} cout<<endl<<endl<<"------------------------------------------------"<<endl;
	}
    
    //-----------------------------------
    //Ingreso de elementos para multiplicacion y division
    terminal* M[8]; for(int i=0;i<8;i++) M[i]=new terminal();
	terminal* Q[8]; for(int i=0;i<8;i++) Q[i]=new terminal();
    if(op==2||op==3){
        for(int i=0; i<8; i++){
	        if(VAr2[i]=='1') M[7-i]->setSignal(true);
	        else M[7-i]->setSignal(false);
	        if(VAr1[i]=='1') Q[7-i]->setSignal(true);
	        else Q[7-i]->setSignal(false);
	    }
    }
    XORgate XORgOP;
    transistor* NOTop[2]; for(int i=0; i<2; i++) NOTop[i]=new transistor();
    transistor* ANDop[4]; for(int i=0; i<4; i++) ANDop[i]=new transistor();
    transistor* ORop[2]; for(int i=0; i<2; i++) ORop[i]=new transistor();
    terminal* XORopter[6]; for(int i=0; i<6; i++) XORopter[i]=new terminal();
    terminal* vccop[6];
    for (int i=0;i<6;i++){
        vccop[i]=new terminal();
        vccop[i]->setSignal(true);
    }
    dobleTerminal* dobTerOP[2]; for(int i=0; i<2; i++) dobTerOP[i]=new dobleTerminal();
    ANDgate ANDgOP[2];
    NOTgate NOTgOP[2]; 
    ORgate ORgOP;
    XORopter[0]->setSignal(r1B);
    XORopter[1]->setSignal(r2B);
    bool signalMD=XORgOP.evXOR(NOTop, ANDop, ORop, XORopter, vccop, dobTerOP, ANDgOP, NOTgOP, ORgOP)->signalBef;
    
	//---------------------------------------------------------
	//Declaracion de elementos y desarrollo de la multiplicacion
	if(op==2){
		ALU aluM;
		terminal* A[8]; for(int i=0;i<8;i++) A[i]=new terminal();
		terminal* mult[16]; for(int i=0;i<16;i++) mult[i]=new terminal();
		terminal* Cout=new terminal();
		int N=8;
		aluM.ALU_multiplicar(M, Q, A, mult, Cout,suma, c, aux,NOT, AND, OR, XORter, vcc, dobTer,ANDg, NOTg, ORg, XORg,NOTx, ANDx, ORx, XORxter, vccx, dobTerx,ANDgx, NOTgx, ORgx);
		if(signalMD==false){
		    for(int i=15;i>=0;i--){
		    	if(mult[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
		} else{
		    for(int i=0; i<16; i++){
		        if(mult[i]->signalBef) mult[i]->setSignal(false);
		        else mult[i]->setSignal(true);
		    }
		    for(int i=0;i<16;i++){
		        if(mult[i]->signalBef) mult[i]->setSignal(false);
		        else {
		            mult[i]->setSignal(true);
		            break;
		        }
		    }
		    for(int i=15;i>=0;i--){
		    	if(mult[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
    	}
    }
	//-------------------------------------------------------------
	//Declaracion de elementos y operacion de la division
	if(op==3){
		ALU aluD;
		terminal* A[8]; for(int i=0;i<8;i++) A[i]=new terminal();
		terminal* Cout=new terminal();
		int N=8;
		
	    aluD.ALU_division(M, Q, A, Cout,suma, c, aux,NOT, AND, OR, XORter, vcc, dobTer,ANDg, NOTg, ORg, XORg,NOTx, ANDx, ORx, XORxter, vccx, dobTerx,ANDgx, NOTgx, ORgx, INV, vcci, NOTi, NOTgi);
	    
	    cout<<"Cociente: ";
		if(signalMD==false){
		    for(int i=7;i>=0;i--){
		    	if(Q[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
		} else{
		    for(int i=0; i<8; i++){
		        if(Q[i]->signalBef) Q[i]->setSignal(false);
		        else Q[i]->setSignal(true);
		    }
		    for(int i=0;i<8;i++){
		        if(Q[i]->signalBef) Q[i]->setSignal(false);
		        else {
		            Q[i]->setSignal(true);
		            break;
		        }
		    }
		    for(int i=7;i>=0;i--){
		    	if(Q[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
    	}
		
		
		cout<<endl<<"Resto: ";
		if(r1B==false){
		    for(int i=7;i>=0;i--){
		    	if(A[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
		} else{
		    for(int i=0; i<8; i++){
		        if(A[i]->signalBef) A[i]->setSignal(false);
		        else A[i]->setSignal(true);
		    }
		    for(int i=0;i<8;i++){
		        if(A[i]->signalBef) A[i]->setSignal(false);
		        else {
		            A[i]->setSignal(true);
		            break;
		        }
		    }
		    for(int i=7;i>=0;i--){
		    	if(A[i]->signalBef){cout<<"1";} 
			    else {cout<<"0";}
		    }
    	}
	}
}
