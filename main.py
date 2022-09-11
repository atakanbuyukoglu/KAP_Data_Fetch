import requests as r
from fake_useragent import UserAgent

website = 'https://www.kap.org.tr/tr/api/memberDisclosureQuery'

query = {
    "fromDate" : "2021-09-12",
    "toDate":"2022-09-12",
    "year":"",
    "prd":"",
    "term":"",
    "ruleType":"",
    "bdkReview":"",
    "disclosureClass":"FR",
    "index":"",
    "market":"",
    "isLate":"",
    "subjectList":["4028328c594bfdca01594c0af9aa0057"],
    "mkkMemberOidList":["4028e4a140f2ed720141164431b905a5"],
    "inactiveMkkMemberOidList":[],
    "bdkMemberOidList":[],
    "mainSector":"",
    "sector":"",
    "subSector":"",
    "memberType":"IGS",
    "fromSrc":"N",
    "srcCategory":"",
    "discIndex":[]
}

ua = UserAgent()
headers = {
    'User-Agent':str(ua.chrome)

}

if __name__ == '__main__':
    resp = r.post(website, headers=headers, json=query)
    print(resp.text)
