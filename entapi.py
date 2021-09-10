import json
import asyncio
import requests
import concurrent.futures
from tqdm import tqdm

data_file = "users_data.json"

annuaire_not_downloaded = False
try:
    with open(data_file) as json_file:
        data = json.load(json_file)
except:
    annuaire_not_downloaded = True

def entget(url,s,headers):
    global pbar
    pbar.update(1)
    return s.get(url, headers=headers)

async def get_users_data(urls,s,headers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        loop = asyncio.get_event_loop()
        users = {}
        global pbar
        pbar = tqdm(total=len(urls))
        futures = [
            loop.run_in_executor(
                executor,
                entget,
                url,
                s,
                headers
            )
            for url in urls
        ]
        for response in await asyncio.gather(*futures):
            user = json.loads(response.text)
            users[user["displayName"]] = user
        pbar.close()
        print(" ")
        return users

def annuaire_download():
    searchsettings = {"search": "","types": ["User"],"structures": [],"classes": [],"profiles": [],"nbUsersInGroups": True,"functions": [],"mood": True}
    try:
        with open('ent_logins.json') as json_file:
            logins = json.load(json_file)
            user = logins["login"]
            mdp = logins["password"]
    except:
        print(" ")
        print("=============== CONNEXION ENT ===============")
        print(" ")
        print("Veuillez saisir vos identifiants ENT pour continuer :")
        user = input("Login : ")
        mdp = input("Mot de passe : ")
        logins = {"login": user, "password": mdp}
        with open("ent_logins.json", "w") as save:
            json.dump(logins, save)
    print("Authentification...", end="\r")
    with requests.Session() as s:
        authr = s.post("https://ent.iledefrance.fr/auth/login", data={"email": user, "password": mdp})
        xsrf_token = authr.cookies["XSRF-TOKEN"]
        xsrf_headers = {"accept": "application/json, text/plain, */*","accept-language": "fr","content-type": "application/json;charset=UTF-8","sec-fetch-dest": "empty","sec-fetch-mode": "cors","sec-fetch-site": "same-origin","sec-gpc": "1"}
        xsrf_headers["x-xsrf-token"] = xsrf_token
        print("Authentification : OK")
        print("Récupération de la liste des personnes...", end="\r")
        userbook = json.loads(s.post("https://ent.iledefrance.fr/communication/visible", data=json.dumps(searchsettings), headers=xsrf_headers).text)
        userlist = []
        for user in userbook["users"]:
            userlist.append(user["id"])
        print("Récupération de la liste des personnes : OK")
        urls = []
        for id in userlist:
            urls.append("https://ent.iledefrance.fr/directory/user/" + id)
        print("Récupération des données des utilisateurs...", end="\r")
        loop = asyncio.get_event_loop()
        users = loop.run_until_complete(get_users_data(urls, s, xsrf_headers))
        print("Récupération des données des utilisateurs : OK")
        print("Sauvegarde des données...", end="\r")
        with open("users_data.json", "w") as save:
            json.dump(users, save)
        print("Sauvegarde des donneés : OK")

def birthDateToStr(bd):
    return bd.split("-")[2] + "/" + bd.split("-")[1] + "/" + bd.split("-")[0]

def showUserData(people_id):
    for p in data:
        if (data[p]["id"] == people_id):
            #print(data[p])
            pe = data[p]
            print("Nom : " + pe["displayName"])
            print("Date de naissance : " + birthDateToStr(pe["birthDate"]))
            print("Login : " + pe["login"])
            print("Email : " + pe["emailInternal"])
            if (pe["profiles"][0] == "Student"):
                print("Niveau : " + pe["moduleName"])
                print("Division : " + pe["classes"][0].split("$")[1])
                print("Groupes :")
                for g in pe["groups"]:
                    print("- " + g.split("$")[1])
            elif (pe["profiles"][0] == "Teacher"):
                try:
                    headTeacher = pe["headTeacher"][0].split("$")[1]
                    print("Professeur principal : " + headTeacher)
                except:
                    pass
            print("Matières :", end="\r")
            try:
                for m in pe["subjectTaught"]:
                    print("\n- " + m.split("$")[1], end="")
            except:
                try:
                    for m in pe["fieldOfStudyLabels"]:
                        print("\n- " + m, end="")
                except:
                    print("Matières : Aucun", end="")
            print("")

def get_groups(name=""):
    groups_list = []
    for p in data:
        try:
            pe = data[p]
            for g in pe["groups"]:
                ge = g.split("$")[1]
                if name in ge:
                    if not ge in groups_list:
                        groups_list.append(ge)
        except:
            pass
    return groups_list

def get_studies():
    studies = {}
    divisions = get_divisions()
    for p in data:
        pe = data[p]
        try:
            div_level = parse_div_level(pe["classes"][0].split("$")[1])
            if div_level in divisions[parse_level_type(div_level)]:
                if not div_level in studies:
                    studies[div_level] = []
                for m in pe["fieldOfStudyLabels"]:
                    if not m in studies[div_level]:
                        studies[div_level].append(m)
        except: pass
    return studies

def get_divisions():
    divisions = {
        "Collège": {},
        "Lycée": {},
        "Prépa": {}
    }
    for p in data:
        pe = data[p]
        try:
            div_name = pe["classes"][0].split("$")[1]
            if not parse_div_level(div_name) in divisions[parse_level_type(div_name)]:
                divisions[parse_level_type(div_name)][parse_div_level(div_name)] = []
            if not div_name in divisions[parse_level_type(div_name)][parse_div_level(div_name)]:
                divisions[parse_level_type(div_name)][parse_div_level(div_name)].append(div_name)
                # print("Adding division " + div_name + " of level " + parse_div_level(div_name) + " and type " + parse_level_type(div_name))
        except:
            pass
    dnum = {}
    for d in divisions:
        for d1 in divisions[d]:
            for d2 in divisions[d][d1]:
                dnum[d2] = 0
                for p in data:
                    pe = data[p]
                    try:
                        if pe["classes"][0].split("$")[1].lower() == d2.lower() and pe["profiles"][0] == "Student":
                            dnum[d2]+=1
                    except:
                        pass
    for d in dnum:
        if dnum[d] < 10:
            del divisions[parse_level_type(d)][parse_div_level(d)][divisions[parse_level_type(d)][parse_div_level(d)].index(d)]
    dbak = {
        "Collège": {},
        "Lycée": {},
        "Prépa": {}
    }
    for d in ["Collège", "Lycée", "Prépa"]:
        for d1 in divisions[d]:
            if len(divisions[d][d1]) >= 1:
                dbak[d][d1] = divisions[d][d1]
    divisions = dbak
    return divisions

def parse_level_type(div):
    if div[0].isdigit():
        if int(div[0]) > 2:
            return "Collège"
        else:
            return "Lycée"
    elif div[0] == "T" and div[1] == "G":
        return "Lycée"
    else:
        return "Prépa"

def parse_div_level(div):
    if div[-1].isdigit() or div[-1] == " ":
        return parse_div_level(div[:-1])
    else:
        return div.split(" ")[0]

def annuaire_menu():
    print(" ")
    print("=============== ANNUAIRE ENT ===============")
    print(" ")
    print("1) Rechercher par nom")
    print("2) Rechercher par division")
    print("3) Rechercher par groupe")
    print("4) Rechercher par matière")
    print("5) Retour")
    print(" ")
    selopt = input("Choisissez une option : ")
    if selopt=="1":
        people_name = input("Recherche : ")
        people_list = {}
        for p in data:
            if (people_name.lower() in data[p]["displayName"].lower()):
                people_list[data[p]["displayName"]] = data[p]["id"]
        if len(people_list) == 0:
            print("Personne n'a été trouvé !")
        elif len(people_list) == 1:
            for p in people_list:
                print(" ")
                print("================= INFOS =================")
                print(" ")
                showUserData(people_list[p])
        else:
            print("Plusieurs personnes ont été trouvées !")
            p_by_id = {}
            i = 1
            for p in people_list:
                p_by_id[str(i)] = people_list[p]
                print(str(i) + ") " + p)
                i+=1
            ok=False
            selopt = input("Choisissez une option : ")
            for p in p_by_id:
                if selopt==p:
                    print(" ")
                    print("================= INFOS =================")
                    print(" ")
                    showUserData(p_by_id[p])
                    ok=True
            if not ok:
                print("Cette option n'est pas valide !")
    elif selopt=="2":
        div_name = ""
        divisions = get_divisions()
        i=1
        d_by_id={}
        for d in ["Collège", "Lycée", "Prépa"]:
            d_by_id[str(i)] = d
            print(str(i) + ") " + d)
            i+=1
        ok=False
        selopt = input("Choisissez une option : ")
        div_type = {}
        for d in d_by_id:
            if selopt==d:
                div_type = d_by_id[d]
                ok=True
        if not ok:
            print("Cette option n'est pas valide !")
            exit()
        i=1
        d_by_id={}
        for d in divisions[div_type]:
            d_by_id[str(i)] = divisions[div_type][d]
            print(str(i) + ") " + d)
            i+=1
        ok=False
        selopt = input("Choisissez une option : ")
        div_opts = []
        for d in d_by_id:
            if selopt==d:
                div_opts = sorted(d_by_id[d])
                ok=True
        if not ok:
            print("Cette option n'est pas valide !")
            exit()
        if len(div_opts) > 1:
            i=1
            for d in div_opts:
                d_by_id[str(i)] = d
                print(str(i) + ") " + d)
                i+=1
            ok=False
            selopt = input("Choisissez une option : ")
            div_opts
            for d in d_by_id:
                if selopt==d:
                    div_name = d_by_id[d]
                    ok=True
            if not ok:
                print("Cette option n'est pas valide !")
                exit()
        else:
            div_name = div_opts[0]
        headTeacher = ""
        people_list = []
        for p in data:
            pe = data[p]
            try:
                if pe["headTeacher"][0].split("$")[1].lower() == div_name.lower():
                    headTeacher = pe["displayName"]
            except:
                try:
                    if pe["classes"][0].split("$")[1].lower() == div_name.lower() and pe["profiles"][0] == "Student":
                        people_list.append(pe["displayName"])
                except:
                    pass
        people_list = sorted(people_list)
        if len(people_list) > 0:
            print(" ")
            print("================= DIVISION " + div_name.upper() + " ===============")
            print(" ")
            print("Professeur principal : " + headTeacher)
            print(" ")
            print("Élèves :")
            i=1
            for p in people_list:
                print(str(i) + ") " + p)
                i+=1
        else:
            print("Il n'y a personne dans cette division !")
    elif selopt=="3":
        # groups_list = get_groups()
        print("")
        # selopt = input("Choisissez une option : ")
        grp_name = input("Nom du groupe : ")
        teacher = ""
        people_list = []
        for p in data:
            pe = data[p]
            try:
                for g in pe["groups"]:
                    if g.split("$")[1].lower() == grp_name.lower():
                        if pe["profiles"][0] == "Student":
                            people_list.append(pe["displayName"])
                        elif pe["profiles"][0] == "Teacher":
                            teacher = pe["displayName"]
            except:
                pass
        people_list = sorted(people_list)
        if len(people_list) > 0:
            print(" ")
            print("================= GROUPE " + grp_name.upper() + " ===============")
            print(" ")
            print("Professeur : " + teacher)
            print(" ")
            print("Élèves :")
            i=1
            for p in people_list:
                print(str(i) + ") " + p)
                i+=1
        else:
            print("Il n'y a personne dans ce groupe !")
    elif selopt=="4":
        studies = get_studies()
        i=1
        d_by_id={}
        dname_by_id={}
        for d in studies:
            d_by_id[str(i)] = studies[d]
            dname_by_id[str(i)] = d
            print(str(i) + ") " + d)
            i+=1
        ok=False
        selopt = input("Choisissez une option : ")
        studies_opts = []
        dname = ""
        for d in d_by_id:
            if selopt==d:
                studies_opts = sorted(d_by_id[d])
                dname = dname_by_id[d]
                ok=True
        if not ok:
            print("Cette option n'est pas valide !")
            exit()
        i=1
        s_by_id={}
        for s in studies_opts:
            s_by_id[str(i)] = s
            print(str(i) + ") " + s)
            i+=1
        ok=False
        selopt = input("Choisissez une option : ")
        studyField = ""
        for s in s_by_id:
            if selopt==s:
                studyField = s_by_id[s]
                ok=True
        if not ok:
            print("Cette option n'est pas valide !")
            exit()
        people_list = []
        for p in data:
            pe = data[p]
            try:
                if parse_div_level(pe["classes"][0].split("$")[1]) == dname:
                    for s in pe["fieldOfStudyLabels"]:
                        if s.lower() == studyField.lower():
                            people_list.append(pe["displayName"])
            except:
                pass
        people_list = sorted(people_list)
        if len(people_list) > 0:
            print(" ")
            print("================= MATIÈRE " + studyField.upper() + " ===============")
            print(" ")
            print("Élèves :")
            i=1
            for p in people_list:
                print(str(i) + ") " + p)
                i+=1
        else:
            print("Il n'y a personne dans cette matière !")
    elif selopt=="5":
        menu()
    else:
        annuaire_menu()

def menu():
    print(" ")
    print("=============== ENT API MENU ===============")
    print(" ")
    print("1) Accéder à l'annuaire", end="")
    if annuaire_not_downloaded:
        print(" (Non disponible)")
    else:
        print(" ")
    print("2) Télécharger l'annuaire")
    print("3) Quitter")
    print(" ")
    selopt = input("Choisissez une option : ")
    if selopt=="1":
        if annuaire_not_downloaded:
            print("\nVous devez télécharger l'annuaire depuis l'ENT avant de pouvoir y accéder !")
            menu()
        else:
            annuaire_menu()
    elif selopt=="2":
        annuaire_download()
    elif selopt=="3":
        exit()
    else:
        menu()

menu()
