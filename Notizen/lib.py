
#------------------------------------------------------------------------------

class Table:

    def __init__(self):
        self.id = [Column('id', PrimaryKey)]
        
    def __str__(self):
        pass
        
    def __unicode__(self):
        pass
        
    def __repr__(self):
        pass
        
#------------------------------------------------------------------------------
    
class Column:

    def __init__(self, type):
        self._type = type
        
#------------------------------------------------------------------------------
        
primary_key = Type()
text = Type()
int = Type()
        
#------------------------------------------------------------------------------

def main():        
    persons = Table()
    persons.last_name = Column(type=text)
    persons.rename('last_name', 'last_name2')
    del persons.last_name2
    persons[...].first_name = 
    persons.mobile_numbers = VarColumn(type=phone_number)
    persons[...].mobile_numbers.add(id=, number=, valid_from=)
    persons[...].mobile_numbers[...].valid_to = 
    
    extended_dates = table()
    extended_dates.id = column(primary_key)
    extended_dates.date = column(date)
    extended_dates.add_row(id=, date=, precision=, comment=)


#------------------------------------------------------------------------------
        
if self.__main__:
    main()