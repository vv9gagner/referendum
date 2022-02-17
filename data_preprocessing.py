 
import pandas as pd
import numpy as np


FILE_REFERENDUM             = "./Referendum.csv"
FILE_POPULATION_2013_METRO  = './base-cc-evol-struct-pop-2013.xls'
FILE_POPULATION_2013_COM    = './base-cc-evol-struct-pop-2013-com.xls'
FILE_DIPLOME                = "./pop-16ans-dipl6818.xls"
FILE_REVENU_PAUVRETE        = "./filo-revenu-pauvrete-menage-2013.xls"

####################################################################################
refe = pd.read_csv(FILE_REFERENDUM, sep=';')

l_COM = list( ['ZA', 'ZB', 'ZC', 'ZD', 'ZM', 'ZS', 'ZX'])

for collectivite in l_COM:
    refe.loc[ refe["Code du département"] == collectivite , 'Code du département'] = '97'
    

refe.loc[refe["Code du département"] == 'ZN' , 'Code du département'] = '98' 
refe.loc[refe["Code du département"] == 'ZP' , 'Code du département'] = '987'
refe.loc[refe["Code du département"] == 'ZW' , 'Code du département'] = '986'
refe.loc[refe["Code du département"] == 'ZZ' , 'Code du département'] = '99'
refe["Code du département"] = refe["Code du département"].astype('str')
refe["Code de la commune"] = refe["Code de la commune"].astype('str')

for i in refe["Code du département"].items():
    if len(i[1]) < 2 :
        refe["Code du département"].iloc[i[0]] = '0' + i[1]
        
        
for i in refe["Code de la commune"].items():
    if len(i[1]) == 1 :
        refe["Code de la commune"].iloc[i[0]] = '00' + i[1]
    elif len(i[1]) == 2:
        refe["Code de la commune"].iloc[i[0]] = '0' + i[1]
        

refe["CODGEO"] = refe["Code du département"] + refe["Code de la commune"]

# Les explications des variables se trouvent dans le fichier : base-cc-struc-pop-2013.xls
col_read_population = ['CODGEO',
                       'LIBGEO',
                       'P13_POP',
                       'P13_POPH', 'P13_H0019', 'P13_H2064', 'P13_H65P',
                       'P13_POPF', 'P13_F0019', 'P13_F2064', 'P13_F65P',
                       'C13_POP15P', 'C13_POP15P_CS1', 'C13_POP15P_CS2', 'C13_POP15P_CS3', 'C13_POP15P_CS4', 
                       'C13_POP15P_CS5', 'C13_POP15P_CS6', 'C13_POP15P_CS7'	, 'C13_POP15P_CS8' 
                      ]
# lire les populations métropolitaines
population_commune_2013_metro = pd.read_excel(FILE_POPULATION_2013_METRO, 
                                              header=5, 
                                              sheet_name = "COM_2013",
                                              dtype = {'CODGEO' : str},
                                              usecols = col_read_population)
# lire les populations des 4 communes d'outre-mer
population_commune_2013_com = pd.read_excel(FILE_POPULATION_2013_COM,
                                            header=5,
                                            sheet_name = "COM_2013",
                                            dtype = {'CODGEO' : str},
                                            usecols = col_read_population)
# concatenate les populations
population_commune_2013 = pd.concat([population_commune_2013_metro, population_commune_2013_com],
                                    ignore_index = True)
# cast les populations en dtype int64. caveat : doing this is losing some precision. 
population_commune_2013.loc[:, 'P13_POP':] = population_commune_2013.loc[:, 'P13_POP':].astype('int64')

# fusionner les populations et le référendum
data_brut = pd.merge(refe, population_commune_2013, 
                     how = 'inner', 
                     on='CODGEO')

# lire les diplômes des 16 ans et plus, attention, pas de données datées de 2013, utiliser celles de 2018

diplome = pd.read_excel(FILE_DIPLOME,
                        header = 16,
                        sheet_name = "COM_2018",
                        dtype = {'rr' : str, 'cr' : str, 'dr' : str, 'libgeo' : str}
                        )

for i in diplome['dr'].items():
    if len(i[1]) == 3:
        diplome['dr'].iloc[i[0]] = i[1][0:2]
# Paris data is split to 19 blocks
diplome_paris = diplome.iloc[32121:32140,:].sum()
diplome_paris.rr = "11"
diplome_paris.dr = "75"
diplome_paris.cr = "056"
diplome_paris.dr20 = "75"
diplome_paris.libgeo = "Paris"
diplome_paris.stable = '1'
diplome = pd.concat([diplome,diplome_paris.to_frame().T], axis=0)

diplome.dropna(axis=0, inplace=True)
diplome.loc[:, "dpx_rec0s1age2_rec1rpop2018":"dpx_rec6s2age2_rec2rpop2018"] = diplome.loc[:, "dpx_rec0s1age2_rec1rpop2018":"dpx_rec6s2age2_rec2rpop2018"].round().astype('int64')

        
# création de codgeo
diplome["CODGEO"] = diplome['dr'] + diplome['cr']

# creater les categories de diplomes
l_niveau_diplome =np.array(diplome.keys()[6:-1]).reshape(7,4)

for level in np.arange(l_niveau_diplome.shape[0]):
    d = diplome[l_niveau_diplome[level, 0]] - diplome[l_niveau_diplome[level, 0]]
    for c in np.arange(l_niveau_diplome.shape[1] ):
        d += diplome[l_niveau_diplome[level, c]]
        diplome['dip_'+str(level)] = d


diplome = diplome.loc[:, ["libgeo", "CODGEO", 'dip_0', 'dip_1', 'dip_2', 'dip_3', 'dip_4', 'dip_5', 'dip_6']]
diplome.reset_index(inplace=True, drop=True)

# ajouter diplomes information à data_brut
data_brut = pd.merge(data_brut, diplome, 
                      how = 'outer', 
                      on='CODGEO')
#  lire le ficher de revenus et pauvrete
revenu_pauvrete_brut = pd.read_excel(FILE_REVENU_PAUVRETE,
                        header = 5,
                        sheet_name = "COM",
                        dtype = {'CODGEO' : str})
# Il comprend beaucoup de NAN

revenu_pauvrete = revenu_pauvrete_brut.iloc[:,0:5].dropna(how = 'any')

# ajouter diplomes information à data_brut
data_brut = pd.merge(data_brut, revenu_pauvrete, 
                      how = 'outer', 
                      on='CODGEO')
# creer une nouvel dataframe en créant les nouvelles variables explicatives
data = data_brut.copy()
data['voting_result'] = data_brut.apply(lambda x : 0 if (x["Choix A"] > x["Choix B"]) else 1, axis=1)

data['POP_FEMME_HOMME_19PLUS'] =  data["P13_H2064"] \
                                + data["P13_H65P"]  \
                                        + data["P13_F2064"]  \
                                            + data["P13_F65P"]

                                           
data['Percentage_POP_FEMME_HOMME_19PLUS_VS_POP_TOTAL'] = data['POP_FEMME_HOMME_19PLUS'] / data['P13_POP']

for i in np.arange(8) + 1:
    data['Percentage_CS_FEMME_HOMME_16PLUS_CS'+ str(i) +'_VS_POP_TOTAL'] =  data['C13_POP15P_CS' + str(i)] / data['P13_POP']

for i in np.arange(7):
    data['Percentage_DIP_FEMME_HOMME_16PLUS_N'+ str(i) +'_VS_POP_TOTAL'] =  data['dip_' + str(i)] / data['P13_POP']

data['Percentage_INSCRITE_VS_POP_TOTAL']    = data['Inscrits'] / data['P13_POP']
data['Percentage_ABSTENTION_VS_POP_TOTAL']  =  data['Abstentions'] / data['P13_POP']
data['Percentage_BlANC_NUL_VS_POP_TOTAL']   =  data['Blancs et nuls'] / data['P13_POP']
data['Percentage_CHOIX_A_VS_POP_TOTAL']     =  data['Choix A'] / data['P13_POP']
data['Percentage_CHOIX_B_VS_POP_TOTAL']     =  data['Choix B'] / data['P13_POP']

# On a remarqué que certaines des proportion sont supérieur à 1, ce qui n'est pas normal. 
# Par précaution, on les a enlevé pour la suite d'analyse.

for i in data.iloc[:,43:63].columns:
      data.drop(data[(data[i] > 1)].index , axis = 0, inplace=True)

data.dropna(axis=0, inplace=True)
data.reset_index(inplace=True, drop=True)
data.to_excel('./data_exploitable.xls')



