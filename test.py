import unittest
from final_project import *


class TestDatabase(unittest.TestCase):

    def test_individual_tables(self):
        x = pull_data_from_table('Bitcoin', 5)
        #Test if Coin ID is right
        self.assertEqual(x[0][2], 1)
        #Test if open is right
        self.assertEqual(x[4][3], 9414.69)
        #Test if Volume is right
        self.assertEqual(x[3][7], 5991140000.0)

        y = pull_data_from_table('Dogecoin', 10, desc=False)
        #Test if Coin ID is correct
        self.assertEqual(y[0][2], 40)
        #Test if High is correct
        self.assertEqual(y[9][4], 0.003177)
        #Test if the MarketCap is correct
        self.assertEqual(y[5][-1], 319932000.0)

    def test_join_tables(self):
        #Test High For two coins
        x = pull_join_data_from_tables('Bitcoin', 'Litecoin', 'High')
        #Test if Bitcoin is right value
        self.assertEqual(x[0][0], 9937.5)
        self.assertGreater(x[0][0], x[0][1])

        #Test Low For two coins
        y = pull_join_data_from_tables('Bitcoin', 'Litecoin', 'Low')
        self.assertEqual(y[3][1], 176.54)
        self.assertGreater(y[4][0], y[4][1])

        z = pull_join_data_from_tables('Bytecoin', 'Litecoin', 'MarketCap', limit=10, desc=False)
        self.assertEqual(z[2][0], 385042000.0)
        self.assertEqual(z[8][1], 7488700000.0)
        self.assertGreater(z[3][1], z[3][0])

    def test_data_manually(self):
        conn = sqlite3.connect('crypto.sqlite')
        cur = conn.cursor()
        statement = '''
        SELECT Open FROM BitShares
        WHERE Date LIKE 'Apr 07, 2018'
        '''
        result = cur.execute(statement)
        result_list = result.fetchall()
        self.assertEqual(result_list[0][0], 0.138524)

        statement = '''
        SELECT ID, Low, Close FROM Bytecoin
        WHERE Date LIKE 'Apr%' ORDER BY Close
        '''
        result = cur.execute(statement)
        result_list= result.fetchall()
        self.assertEqual(result_list[0][0], 2)
        self.assertEqual(result_list[6][2], 0.002345)
        self.assertEqual(result_list[4][1], 0.002035)

        conn.close()

    def test_join_manually(self):
        conn = sqlite3.connect('crypto.sqlite')
        cur = conn.cursor()
        statement = '''
        SELECT Bitcoin.Open, Litecoin.Open
        FROM Cryptos JOIN Bitcoin
        ON Cryptos.Id = Bitcoin.ID
        JOIN Litecoin
        ON Cryptos.Id = Litecoin.ID
        ORDER BY Bitcoin.Open
        DESC LIMIT 10
        '''
        result = cur.execute(statement)
        result_list = result.fetchall()
        self.assertGreater(result_list[5][0], result_list[5][1])
        self.assertEqual(result_list[9][0], 8736.25)
        self.assertEqual(result_list[5][1], 168.72)
        conn.close()

unittest.main()
