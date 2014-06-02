import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

class PythonOrgSearch(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()

	def test_clickCreateEvent(self):
        driver = self.driver
        driver.get("127.0.0.1:5000")
        driver.driver.find_element_by_xpath("/e/create").click()
		
	def test_clickHome(self):
        driver = self.driver
        driver.get("127.0.0.1:5000")
        driver.driver.find_element_by_xpath("/").click()
	
	def test_clickUsers(self):
        driver = self.driver
        driver.get("127.0.0.1:5000")
        driver.driver.find_element_by_xpath("/u/list").click()		
	
	def test_clickMyEvents(self):
        driver = self.driver
        driver.get("127.0.0.1:5000")
        driver.driver.find_element_by_xpath("/u/events").click()	

	def test_clickLogOut(self):
        driver = self.driver
        driver.get("127.0.0.1:5000")
        driver.driver.find_element_by_xpath("/logout").click()			
	
    def test_input_createEvent(self):
        driver = self.driver
        driver.get("127.0.0.1:5000/e/create")
		select = Select(driver.find_element_by_name('eventtype'))
		select.select_by_value(Group)
        elem = driver.find_element_by_id("name")
        elem.send_keys("TestEvent", Keys.RETURN)
		elem2 = driver.find_element_by_id("Users")
        elem2.send_keys("Tester@test.at", Keys.RETURN)
		elem3 = driver.find_element_by_class_name("form-control")
        elem3.send_keys("01.06.2014 23:41", , Keys.RETURN)
		driver.find_element_by_id("createEvent").click()
		
		
	def test_search_Events(self):
        driver = self.driver
        driver.get("127.0.0.1:5000/u/events")
        elem = driver.find_element_by_class_name("form-control input-sm")
        elem.send_keys("TestEvent")
        elem.send_keys(Keys.RETURN)
	
    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()