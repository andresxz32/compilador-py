false = 0
true = !false

n = 2
while(n <= 100){
    isprime = true
    factor = 2
    while ( factor * factor <= n && isprime){
        if(n % factor == 0){
            isprime = false
        }
        factor = factor + 1
    }
    if(isprime){
        print m
    }
    n = n + 1
}