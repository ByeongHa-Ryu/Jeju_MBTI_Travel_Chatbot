def update(query):
    file = open('data/num.txt', 'w')
    file.write(query) 
    file.close()

def last_addr():
    file = open('data/num.txt', 'r')
    last_str = file.read() 
    file.close()
    return last_str