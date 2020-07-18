import uuid

mylist= []

idi = uuid.uuid1()
# print(idi)

mylist.append(uuid.uuid1())


print("The id generated using uuid4() : ",end="") 
print(mylist)