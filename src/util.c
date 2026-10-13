#include "aden.h"
HIDDEN void* memcpy(void* d, const void* s, size_t n){u8*a=d;const u8*b=s;while(n--)*a++=*b++;return d;}
HIDDEN void* memset(void* d, int c, size_t n){u8*a=d;while(n--)*a++=(u8)c;return d;}
HIDDEN void* memmove(void* d, const void* s, size_t n){u8*a=d;const u8*b=s;if(a<b){while(n--)*a++=*b++;}else{a+=n;b+=n;while(n--)*--a=*--b;}return d;}
HIDDEN int memcmp(const void* x, const void* y, size_t n){const u8*a=x,*b=y;for(;n;n--,a++,b++)if(*a!=*b)return *a-*b;return 0;}
HIDDEN size_t strlen(const char* s){size_t n=0;while(s[n])n++;return n;}
HIDDEN int strcmp(const char*a,const char*b){while(*a&&*a==*b){a++;b++;}return (u8)*a-(u8)*b;}

static void put(char* o,size_t cap,size_t* n,char c){ if(*n+1<cap) o[*n]=c; (*n)++; }
HIDDEN int aden_vsnprintf(char* o, size_t cap, const char* f, __builtin_va_list ap){
    size_t n=0;
    for(;*f;f++){
        if(*f!='%'){put(o,cap,&n,*f);continue;}
        f++; int zero=0,width=0,lng=0;
        if(*f=='0'){zero=1;f++;}
        while(*f>='0'&&*f<='9'){width=width*10+(*f-'0');f++;}
        while(*f=='l'){lng++;f++;}
        char buf[32]; int bl=0; u64 v; int neg=0;
        switch(*f){
        case 's':{const char*s=__builtin_va_arg(ap,const char*);if(!s)s="(null)";while(*s)put(o,cap,&n,*s++);continue;}
        case 'c':put(o,cap,&n,(char)__builtin_va_arg(ap,int));continue;
        case '%':put(o,cap,&n,'%');continue;
        case 'p':v=(u64)__builtin_va_arg(ap,void*);put(o,cap,&n,'0');put(o,cap,&n,'x');
                 do{int d=v&15;buf[bl++]=d<10?'0'+d:'a'+d-10;v>>=4;}while(v);break;
        case 'x':case 'X':v=lng?__builtin_va_arg(ap,u64):__builtin_va_arg(ap,u32);
                 do{int d=v&15;buf[bl++]=d<10?'0'+d:(*f=='x'?'a':'A')+d-10;v>>=4;}while(v);break;
        case 'd':case 'i':{s64 sv=lng?__builtin_va_arg(ap,s64):__builtin_va_arg(ap,int);if(sv<0){neg=1;v=-(u64)sv;}else v=sv;
                 do{buf[bl++]='0'+v%10;v/=10;}while(v);break;}
        case 'u':v=lng?__builtin_va_arg(ap,u64):__builtin_va_arg(ap,u32);
                 do{buf[bl++]='0'+v%10;v/=10;}while(v);break;
        default: put(o,cap,&n,'?');continue;
        }
        if(neg)put(o,cap,&n,'-');
        for(int i=bl;i<width;i++)put(o,cap,&n,zero?'0':' ');
        while(bl)put(o,cap,&n,buf[--bl]);
    }
    if(cap) o[n<cap?n:cap-1]=0;
    return (int)n;
}
HIDDEN int aden_snprintf(char* o,size_t cap,const char* f,...){__builtin_va_list ap;__builtin_va_start(ap,f);int r=aden_vsnprintf(o,cap,f,ap);__builtin_va_end(ap);return r;}
