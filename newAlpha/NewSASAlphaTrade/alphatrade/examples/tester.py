from ShoonyaSession import createShoonyaSession 

class ShoonyaAPITester:
    def __init__(self):
        self.shoonya_session = None

    def test_shoonya_session_creation(self):
        global shoonya
        
        try:
            if self.shoonya_session is None:
                self.shoonya_session = createShoonyaSession()
                print("Shoonya session created successfully!")
            else:
                print("Shoonya session already exists.")
        except Exception as e:
            print("Error creating Shoonya session:", e)

if __name__ == "__main__":
    tester = ShoonyaAPITester()
    tester.test_shoonya_session_creation()
