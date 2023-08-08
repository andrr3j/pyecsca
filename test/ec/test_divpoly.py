from unittest import TestCase
import json
from importlib.resources import files

import test.data.divpoly
from sympy import FF
from pyecsca.ec.divpoly import a_invariants, b_invariants, divpoly0, divpoly, mult_by_n
from pyecsca.ec.model import ShortWeierstrassModel
from pyecsca.ec.params import get_params


class DivpolyTests(TestCase):
    def setUp(self):
        self.secp128r1 = get_params("secg", "secp128r1", "projective")
        self.model = ShortWeierstrassModel()
        self.coords = self.model.coordinates["projective"]
        self.add = self.coords.formulas["add-2007-bl"]
        self.dbl = self.coords.formulas["dbl-2007-bl"]
        self.neg = self.coords.formulas["neg"]

    def test_ainvs(self):
        ainvs = a_invariants(self.secp128r1.curve)
        self.assertSequenceEqual(ainvs, (0,
                                         0,
                                         0,
                                         340282366762482138434845932244680310780,
                                         308990863222245658030922601041482374867))

    def test_binvs(self):
        binvs = b_invariants(self.secp128r1.curve)
        self.assertSequenceEqual(binvs, (0,
                                         340282366762482138434845932244680310777,
                                         215116352601536216819152607431888567119,
                                         340282366762482138434845932244680310774))

    def test_divpoly0(self):
        # Data from sagemath
        coeffs = [11,
                  0,
                  340282366762482138434845932244680302401,
                  211962053797180672439257756222135086642,
                  340282366762482138434845932244678441564,
                  115415922367823003571854983213102698477,
                  152803211743444076787231275062278784385,
                  68540219804769369063918923691867278088,
                  43207172520353703997069627419519708522,
                  83208285732019037267730920881743782729,
                  93286967763556583502947234289842152563,
                  324950611928652823046744874201355360259,
                  244242343224213805514200367379671854852,
                  307096814154284337284845014037169929735,
                  180946781765592277412990188457219828893,
                  301253861469456022084288029442105687698,
                  58053323975526190296189278379252064657,
                  224437885189054146208302696540070489578,
                  281987318191429654256483850017931541622,
                  21449216018131966691124843738286677726,
                  10958264881628724646042625283328121348,
                  104868338562600481545003572552335444641,
                  127205813185570107009206143413997395181,
                  116865717360861207318274706645935808417,
                  281460458922812844939222119784601506753,
                  336607098463310980140968249747513775735,
                  304486486784143285234063826161805094682,
                  194935097339732797131694429642153881938,
                  193523171473792085604518744912658246509,
                  204844449336357293979832621297234119270,
                  244481753281744913785581086721299830802,
                  46816299473081369405217767361380254657,
                  303070923752707405164354702252828590781,
                  222516549119176621389776816552836322766,
                  292006660232236762950883960515487362063,
                  53617127992846936725441702182362940200,
                  242498306026562585655027965022211017540,
                  25039963304689451659955607939868533124,
                  328580435950647191774558154445103295305,
                  24226614081978788956695324769468902511,
                  147945052666123617872720080832548744564,
                  287190187011075399698210761813202261601,
                  117131681517270554750959286838283723521,
                  35018410385280384289320020556813474742,
                  83939964512240352730304831725346032711,
                  147219996946006689656600631222993527180,
                  280430477096741745234510250577626566690,
                  32753113267385981127807026368593329576,
                  105134319561523011785486683031223863934,
                  206456116679151691099661865534540095270,
                  116180470443213022739312068090342951131,
                  245850120846480965440408943459023315919,
                  45805943896736805301879725516256422457,
                  226777421435695229777151315574975350291,
                  283680841707610526659029980964566557627,
                  53168487339451866167506032177471934158,
                  69212302225932892622760219621519562036,
                  183916411340675637978873336955593385541,
                  119478537598919956688656337369481692789,
                  234767298887335988751880131162396819780,
                  218412162101425422347176804186940045781]

        K = FF(self.secp128r1.curve.prime)
        poly = divpoly0(self.secp128r1.curve, 11)[11]
        computed = list(map(K, poly.all_coeffs()))
        self.assertListEqual(coeffs, computed)

    def test_divpoly(self):
        # Data from sagemath
        K = FF(self.secp128r1.curve.prime)
        coeffs_0 = {
            (0,): K(16020440675387382717114730680672549016),
            (1,): K(269851015321770885610377847857290470365),
            (2,): K(340282366762482138434845932244680310693),
            (3,): K(109469325440469337582450480850803806492),
            (4,): K(340282366762482138434845932244680310753),
            (6,): K(2)
        }
        self.assertDictEqual(divpoly(self.secp128r1.curve, 4, 0).as_dict(), coeffs_0)
        coeffs_1 = {
            (6, 1): K(4),
            (4, 1): K(340282366762482138434845932244680310723),
            (3, 1): K(218938650880938675164900961701607612984),
            (2, 1): K(340282366762482138434845932244680310603),
            (1, 1): K(199419663881059632785909763469900629947),
            (0, 1): K(32040881350774765434229461361345098032)
        }
        self.assertDictEqual(divpoly(self.secp128r1.curve, 4, 1).as_dict(), coeffs_1)
        coeffs_2 = {
            (9,): K(8),
            (7,): K(340282366762482138434845932244680310639),
            (6,): K(187545273439985507098415273777631738640),
            (4,): K(117928913205007755574446043156465405646),
            (3,): K(244159722710157842132157548160645018307),
            (2,): K(200234655086793134086408617236124137371),
            (1,): K(51914434605509249526780779992574428819),
            (0,): K(60581150995923875019702403440670701629)
        }
        self.assertDictEqual(divpoly(self.secp128r1.curve, 4, 2).as_dict(), coeffs_2)

    def test_mult_by_n(self):
        # Data from sagemath
        K = FF(self.secp128r1.curve.prime)
        coeffs_mx_num = [1,
                         0,
                         6,
                         250332028321891843231386649625583487328,
                         9]
        coeffs_mx_denom = [4,
                           0,
                           340282366762482138434845932244680310771,
                           215116352601536216819152607431888567119]
        coeffs_my_num = {
            (6, 1): K(8),
            (4, 1): K(340282366762482138434845932244680310663),
            (3, 1): K(97594934999395211894955991158534915185),
            (2, 1): K(340282366762482138434845932244680310423),
            (1, 1): K(58556960999637127136973594695120949111),
            (0, 1): K(64081762701549530868458922722690196064)
        }
        coeffs_my_denom = {
            (6, 0): K(64),
            (4, 0): K(340282366762482138434845932244680310399),
            (3, 0): K(78075947999516169515964792926827932148),
            (2, 0): K(576),
            (1, 0): K(106054522763933629886951553464196514339),
            (0, 0): K(276200604060932607566387009521990114935)
        }
        mx, my = mult_by_n(self.secp128r1.curve, 2)
        mx_num, mx_denom = mx
        self.assertListEqual(coeffs_mx_num, list(map(K, mx_num.all_coeffs())))
        self.assertListEqual(coeffs_mx_denom, list(map(K, mx_denom.all_coeffs())))
        my_num, my_denom = my
        self.assertDictEqual(my_num.as_dict(), coeffs_my_num)
        self.assertDictEqual(my_denom.as_dict(), coeffs_my_denom)

    def test_mult_by_n_large(self):
        K = FF(self.secp128r1.curve.prime)
        mx, my = mult_by_n(self.secp128r1.curve, 21)
        with files(test.data.divpoly).joinpath("mult_21.json").open("r") as f:
            sage_data = json.load(f)
            sage_data["mx"][0] = {eval(key): K(val) for key, val in sage_data["mx"][0].items()}
            sage_data["mx"][1] = {eval(key): K(val) for key, val in sage_data["mx"][1].items()}
            sage_data["my"][0] = {eval(key): K(val) for key, val in sage_data["my"][0].items()}
            sage_data["my"][1] = {eval(key): K(val) for key, val in sage_data["my"][1].items()}

        self.assertDictEqual(mx[0].as_dict(), sage_data["mx"][0])
        self.assertDictEqual(mx[1].as_dict(), sage_data["mx"][1])

        self.assertDictEqual(my[0].as_dict(), sage_data["my"][0])
        self.assertDictEqual(my[1].as_dict(), sage_data["my"][1])
