#ifndef terminal_h
#define terminal_h

struct terminal{
	terminal* sig=nullptr;
	terminal* ant=nullptr;
	bool signalBef=false;
	bool signalAft=false;
	
	void compSignal(){
		if(this->signalBef!=this->signalAft){
			this->signalBef=this->signalAft;
		}
		if(this->sig!=nullptr){
			this->sig->compSignal();
		}
	}
	
	void setSignal(bool signal){
		this->signalAft=signal;
		this->compSignal();
	}
	
	void conectarTerminales(terminal* t){
		this->sig=t;
		t->ant=this;
		t->setSignal(this->signalBef);
	}
};


#endif
