from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Callable

import validate_model_orchestration as validator


SIGNATURES: dict[str, str] = {
    "sha256:0dac3e42607d364d6147b3f5c3dc12952dd8fa073f622c40e48e8375d43a2eff": "dwb76eftwHVY2+hznIsek/NzeArX/zQ3YSyt5W1tEb9t8v8UE1UHII4HhPlBWog/1ssZIdKxpaEFrkB9mV2PykEOBz60KKtas+hE+u7wcMQBW8r3vuHB0yk2tsXttQrTPZ0Qb2uXQEgfoAL3NRJeJm1ftXGMvAKxXHgpS3mv3B+usgQUw8FeXNIKEWL3XBANzYZFbNZYV8Vndm7NRNDsuLUkQS0yDQE0mZYDQ27uWMyArEgpWfou8ReFqnQlj/Dk78EWf2uI7rxmdlnMrVvWHm8KwouhfV8gjTfUcZ/rxfB3FPzVKPyeFQA/ys6Km8ZH2EUxup3o4CwR0LpXR1KNkA==",
    "sha256:49294da4c1b4a0266041ae75292fdc51d2e205f436612a98b9b0897d0357e9a5": "nqH/pThfXMEhP7bAHYJYLppUYentXwIfc/PG+iDii+kHEFCXkIN8wunGEcDTSLoIDLzGttSGpQnja/ZSPFgm1/KpcCCvnwykamsMf9d9spXBYzQUvsy3pzXC5hMiT8H0lPYAisjRD1orrd5K3dE1XN2p5vIVS0kJ0QIV7ywBSMZfpD29KD27BhY3lpReeuvv40UcCcE+u1O+oG45eatg37uai+IPxdFIhujTA8t1HPFgxBv8Vay7yLKelF537lXpIb5krxKFZiZPH9VuLEuh93WmBUkJI5dCGExFzPXPXm28XpC+agZOZ/FNAzh4rqQhHw4A7urEOPtGYYbPH8xgow==",
    "sha256:5af558946b7329637be5e96803e9aefb2ce3569fdc588d7c3fa28f002677be32": "fm5BXFJdNmaVpidqVOnDT5g4hkIofniN3aMXsNC8ojenEgjZ5vcX2/psSVuQb4WLm5ofDbCwaMT/YYR1bf74aaTZS8C+jhVnIeXUNZf0KfhIRTb8D7hNBXJF9clj80JmOwtTjgny2sg8LiaX72Z33XwgIDh5Wlbs4axQa3LrJEXw3RgKmALTHaATf45nshzuZYzbYQd23VVLPjVjsjtgS4fUaQcjEPD+7yoL9enkypkIwUa0XdTAeTENH5ygu85NZuzjfo8eliiucf4vluJDZ8I6ijUfsiPBxfMK87gKgESvhrTPX0iH/N1T39rUmmU82sxptw1LAk0Fpg7KWsgsFg==",
    "sha256:60d54c8952e7f181a6d6933b1bda5f6d404a44cea248541eb14849d272fc3b9e": "VeFR6Ak5nHuDB8rgcdw7HfctNKNdFhNWKY2oa4qXttVTuka/9Upv1oERNaM1qrOTS+OJdMjNG4w/GJKM/euXNEY0XWEKrwTSeTZja6S3/pFjcihq0KFNGHxgDgL+wRGRpvvhbiPP/fAAOnb50wPdq1Tdr5pKDRozBoG84Uax2VxO8oFnTvIA23f6pCCrRng+g4TACg7uNsxAWRU6r8WBtritgLFFWOh4JqoC8fmWxwAALvUmo6legaaw+Am0sdN1BPAMTwpIb6Y6VRMg9Fus2ykZyFLFyYkgYORxDvii5+mdk9j/AcpYHqbOdRDFUJQatu0gn0KzDZHQOAS/kQM7qg==",
    "sha256:6de5653b0cf946dd7fd474f6bd48917b41818c25634d92be9e194e1e6a8eb09f": "jaHtUrmfqY1oB4ylS9pvROip2+0aE7CQ83ZoeeovfH0CVdA/W48FRp6DTyNwC//BILq+r/rqX1Z+DlHUvFEMmVU+b7liS/MkF9cRSQByv4JvLAINM5MvGPYx3OhonzCSfLbWIdzkOZw2sWySEYL30eC1/C4kZ6Cdc2ganDVukwr2W/3pgBkSCK6909kvmt1eycujAUwrtbbykGTo9gncc7yy0fCpYK0xd1JBXoRq2CDL41agLgnhtsALeCPQKZm9zixltPuHWvP8AUsjgo18wyb3x0OFN5+SBpBKguglCqavvDRzusbazqSujX3EejpbFq9v+/lSsYeizlnivbsmbg==",
    "sha256:7db5cdf3299c9c2e0bce4f428e33eaae56bded314ebbefc444e285fa9d476a30": "rxspDmHdYNoneboUzpJ/gFQSEZpsOPizGytRHw0tiWZd/z971plXbynjiP6Qt7mcWQEheGE8NXPqn2ra9nGStbFzUcL+jl+9bwP8KE2Y7EnvojxgREj/gndTWIjiHWHgBSB1P5UeHD6/Md92RiryW10c5UUl1FbUld9armkGYFze3O+WkwFbicZ5w6ME6A4eFDkhw4/Gorgeyn/9YHvMXti2o0ucjMOlg98nN/WPRY5E6qFZ0PNIrR+WkFldN3h5oy3fXZUb55SK7wpHQyVX9rElHmagqSnujYxVcnx+9gMwyNdPlnTzc2mIeTAwNfSMtPbpOIQFn6ef1ZqLzeYySA==",
    "sha256:ae1cb443929c1522c7f1d577705e4040915178fd4ead00fd0672832f00675bb0": "VanvJg4+azRJCerGwgBOHyPeera4gLTVto3z3TJePjGuYgI3fwz+BSIo20xKYCctF0CQu9YWHgG4NJQWbpi8xO/LQB+whLVrWHv/AXuQ1Uo/FTTyMBPxftVfyTdR3/sno/S8lrbsXS4uyAOBqIDpaalAKryiI12Fbv05OaZfTy9t6sfGZeJLL2cI3f4Dk79DU4vZNfAvW5inwVVSj3kcGIkYlMYb9oWmxcYDOQThoba0QOg9ibSMouXS5XWD5ISQ6RweaUpI8EaeooT+WJjKTr5gCzC0Jr1AVKrcZu/34sJJ049sek/zOyaqgQss3HbFbjTio+wpZCyQ9RXSFgg5oA==",
    "sha256:ec7204e0f4dbe47783cdeb2d8cc21ba035f8657e0c015f31bca9d1982aa2d061": "YZlVslLMeP58mhNfaFBIy6dNhTbAeZFiJQlvLX/Hc93FbrILqM0ALAEux7xdOLUDaeVWkp7AyYGq+TDvnFbanN3KZKKh3GqqDhCTp5Oks7HmOGQg+1jCs1TUUElO5XiObyYHZthALOk9SPGslBdCI3qSFeJO+xHaNCaUCioifZL9DNKZzqn+tHljpsjzpYbY9wSFdun7WuGTSYicM1+Q/R760MNSQ3MXKiiCGwiNR1ZVnA/19PzegWr5F4hZHCndiSS5elT45Wa9Z6yHNuES8zVgNy35+oB0McXD/DjlWb6NsIDD1sfa2hKNaghh2iA+DRsgnWpFtOPNOmD/OgZDEA==",
    "sha256:00bd1c76bb770f034851434cdbc8c740379203148d1e3be75208275a1be2d2c8": "MxW9rFMIRIBuGV6oS5SyqZQZDhqJ2/D2SB55oeWSD4fgUuIuiB9ZcjvTbD4UnrfZyuar1lzVTIYGdpStC/bbUeQ8GLAHqhVdRJJm5WVnzD5P0NePW9H1uBdz4/J8eKpHXcTDySbxXpRhub7OB/aoJwVqSpGNh7utNiGEVUtu8BZ2KKVaZljXqJEnlkGOxA+73ySjRHvNJp8r8uExQhHvGtR6vHpSI1QnjnIaXNMnolijey5e3+9BjpTvjcLltiBE3I/l2zOT7zjSzBCI7pxcNqXbfO9gwQxqZKgs5qWuOShSWDQPWD+LniSBdgrCBOPmp/XLaD9THFxHBj+hu8PHbQ==",
    "sha256:15eab6ced7c718d09ae2169dfd5f5f79291dc0ba2ce5df47812b6cb64e64475a": "Rb4oYOJdBMUrjf9LingpQA/snIh4FscPX5rrDSsmT6ir9YToFSH5MLg+euEWW4TMPVAyJZr7xBXoWJJpyAgoe94B8vdoifrCr3rtJZwEzZolzVMrNOVd1QK6sgAjsOiEM4IbwtxLObEXETuP1ObalWL2B4MQ5cONlXXSHbfEc7mlhJUXhLvTy67HskpqdN04vSCdgtq3jSz+ttCu5TVvVAEcsuVXSLUGev9WhI3c5MHef3jCaCRat13a0PABoRdjMo53ZtJyod/DYnSDjmo8Sds0/+wB2kalrbIlWDFuIXRe1Z74K/8IcU0d1wVtdDMrEyPA2poxEVACWvpZltW41g==",
    "sha256:2a55e4a6390bf47c071f73ae996bc6eb610b970284f7163d028af4166f6b49ca": "MZ3cIz+FWLFSD1EyZVeOpb99ZBRtA5XTqTpkl6p02CdnLW2z1NXKCg/nTXpL6OIOP/gOyQfaTFoE5T/EOdm/PzLdel83hwdyhsLOtpeb24g+wNi0YKteZDNLDgLMr1E2lDEESKWE5/IHBJHwcFg2b66I2lqIttFzxB0GGHRspu2E2HM60I0JKSP+LhmFCkMCZ6w9VOcmiaUGvv4/5YGCa6UVhnJA2gy3FuvWQbgaVfTUUo+bu31QgwdSttqkB8Dfn+xze4atAv6t8NgYqtjNRkGA66KN/E9DxPbh1C2p5x9ZnCmcZL+LQE8qwhpKTT7KiBEyNiJiyOtzhyDk1ZLo/w==",
    "sha256:2bf677275c3bae5fb2b31c25e42d40009eecc25ed9846886678e7c86e2459ed7": "XaDcPxQku9y2PCJotBu4Er+CXerxIeWhGrsgJ7SBOCJKqNb/EDB8CjBarsucWyXoC1ic5y/oATg5e/WkQhea4i4cIiVGyAddAfkgnoG2xvs6rdGqg2U/4qa4B0xXTMXl3chobOgHKNIUyRx6bmjbqbOUeZF/zwU5o4BVWaPWX44ZmVr7W7YnB7fLPPYZaBOGxbc+38xk1RapyiuUyXZC2LIkvGCGG8E6jcCdRcC1OZNX9C0zmHoWk3L5q8HwT1b050dxvNO/TK0fSMhszbpgxjnZCfuRAu7AkoVh+PvGD2Mb8YgL8FEG22Nh8wzpqNzdnbFuWhAI7K7N7O3pdqSqsg==",
    "sha256:435e21a4b2fda2d90b7f5013b01ea9b8f27ed73e54170c70ed0587b8dbdafa31": "NyPnAAdwRbnb6MiQx+hU7UiKSH7rbOxN3VQPkcMTZYc4802ZuoA/VhXYJDR4VBet2zyzMONY3V7PyWsw59oat9d5jw5dsiyTfqh0Lez+BI4OI8wCkqYTqrCeY7+woPQ+2dBzeavjH7/dQlxFZwZQ0F4TAqyHY/Ky0V+MOr8vxFVOZyIuxXlMW7mCETclcOTz60EwG+A1xY4wZlKUcXGC7Ih6fPK0f9ANqz7Y02GlMY66oni96RVRrnbBa106dpQ+ciSKzREC8BPZcPLB8Y6XTLOUTBnC3tkcyAiHg6QZ7vtJt2iltAvMqXu16JDcJUU4vY4ldSjlLkl8hyQEANmWTw==",
    "sha256:583ad923ed76435b99da891ea76f7bb172ae51f75204fc935915bb05b84d1a81": "Ov2IqVQ26WxtVXVx9AAzKXw8yX/gfRD1qTsQ7w9ZLCscwnsz5o9wfHhn0kcpHMPhIoxYBa9v5YYq+GD+hDHCXRIt6f27InbO369uRrMk/k+fE+FgaZ7zVEzkKTMJC1GTdrfSePKw3TNT8lsrpFVeodR9iRXTLAwVgIOLpAxj8j07hon6t/9Y7SBlE5Dc8SaincunpS8uGSKITE2rf8NutrMuTTs79NDJodFBbw89hLURs51gO8IL8VeTHV99jALngOFdCGSinnO94IDZ4o+LMF+Xv4iRXOhUB218JpX434xQDPlmSDT15RkDc15oKkKEW6g2ISuc2lJvG2fRmbv9lA==",
    "sha256:5f7f858f1cda3f2b7ed5e8affa61b84f207b224513b4a9973758a1146689cfba": "KWod+JEqU3Eg9y+CwXLjx/oli3ivF/v8GxMTdL/ZKZb7nYHlwSA4KXW51n11dd1dpbBU1Wmq+A047NdaL8m3YTZ9GGNDrX7/0CEZxldwoQxXAmyTc53Wi2UiygOoUd+g/xOz2zC05tZ6SxR+8rjIma5UMD9BdFsKjWBhGUNx7WuQ4eO323dEnyHqQa3rJgpC4Hqd5BNOUzlaTw7GhfJVyqFdbrW2kBED5ZbeQ4sah8d7GXwC6MBjaf1yXC6Ko2s71gTLUW8RWijajv+WrJF2D9FKoEbHuoEgik340BiOcEBzeZAVNZ6ur2anIk3HrMfdlg9xJOvZBraBifklTpZvgw==",
    "sha256:6694d262d149cffa63be8510af8f0b2519dd25425d50f62e3ac1430ef732a981": "JEk3B0+p2ekEC9SNxunv1wIIEKgAwA91duwJE1Zsfl2ZQLVytc/gMVkPSd2ssUA289U8zGYllcSAonSOr9orAnoGSIm9e+66+IRHVR/MCPdrZVoRqsUeVr1B6ElodvBsMegfI03vAUNTyY7eVvkGvKg6UbdNeQ0slF4tai3NFcAOx1TJ+DBFKx77kYqusCQXa+ORLcC2Gy2RgChmCy8dgrOPVsyLhw3bhg4MqDtkEC/fGunzxx6EiXmk+wTCuL/+onlxojHsMAm5tGcNB2kKH0P7ZXEKXm7bw2fKVSY/CJ8vBCc6wjxcT2s3JF+VNVvrMcQ3WCe2cvf52/sQaoio3A==",
    "sha256:85c4e806836117422927f4701e040713a7ebf7273bdfab818f2900bf7de5d3e8": "lzmPAD07YrfZowzkkr7o36RMivE06yn1be3QkAufPrDigLeWJlqAXyjnFoI/azlo2t8Wo/eA/Ce3McNnd/Ylal9qFAjbjXaBkJCveLtSHHndqp6EV3oo4wX8kCvOYyzWMZiUrDZSpvsL26zIn2Fs44oixkdYRs+R0ImJs/zPjxLsEIcw+jz57ti+ul95I2QONAWHC1uLMoGW0rKhTz9/dukQqs2xiW8+7Nbt8c/XxJ6Z5jUXFqP8/vqYdIrGRbelZqqVIKrEyNYkcNbyq9KOs3iPjEJ3dZWCdCtH+ZO/8DhSUoE9prvpeeN/5CrH6YMKwWK2T/luJcLtwC79frKRhg==",
    "sha256:96e0bb93a485d7de008932bdd229848f2275a3fd78cf352bf6c64d9b09327d54": "Aa/XBvMLqExIbHhv5+y968k120chjTagc5iPxvcmGvTRZm0m2KYwEfxM2oNcmeI6+XP4FcsJIROel/xZNk6Z1Kvd0Sw7SB9WFdWmYmQdTeLKF+/myaNE9MwUc+KgP1lcgHQzdyQSJ/UvFHHWve/ISg+Ihoks3DNCkEQjaqTgx2h+cdMlefqftYtBK2St9kHbltRd3n3yo99HwJFJY1tZGYscrxMlNI4V9OSICc2QaRbVP56D/QSnGZ7Yk4J4tUhggPGoRK/yZPyYBk3jCfPN2Ww+IRrdo/Ro6+6jpxnUwXaHqvrxe9ZufhcyCsfW4dn9TUE3xLC/7kIEVMAaQGyVmw==",
    "sha256:a1691aed48fe456b0ba9d40cec318482690307bf3a67d91016f3a4b0a01b4ec0": "BottbauKvxmvWEZo3VEE/qGSYbV+GJSZtX7b8qLxP8tOY3Eh/6kVeyusEP5329BU1cie4mvcgiN1no5RcJpir9kFo9kdLvcYjKoEPC6gdxDsOklKEHJLU3Zv4CKKban0pS36VoZwPPRvnq2ekK4VyMoKAG9xR5jrmoQHnLC6XEVY3UlMJjkXbqjFlPZOSUTY7NUmB/ecBhwdVtQ1IWZNj5YasO7YPR+Wp+O+zZKgghpXMtbl1PjpoMU3JdhoT4y5NMXtQzFn9BPHLfP7wM+dsqHtEONa8PVn4s7QPetUIkp8LcKVsHuLJ2DgqIKvYG40DUf9rmNMxiKgAnhj0BmnNw==",
    "sha256:b0cd21c2d1240e58363d943c01e896c82c9e2d039700d13bd5ed0a9c09f43c59": "V+QG1TZNnUYtkKvDj249jfwyApuuDGtNP3TKcI/zk1tbsYVqYo1GN7L3SjOiOQjwynIgwB1ImfXBaIePDlPVc6QwaMcwX71hr626gbIaE8vkllWB9xXrv38L8iU9bUkrTPgO5b7+LJijvIsw2OAYmkWQvQ44U+TVNJb/9p/lxzAoQd9d1d90fw6r0TknrAK7wSFwow5jTzFeGTMMZSnJQM2TJFru6Otn8vMFxf9xb7+CQuBirZFDYi7C8lYaY1krCcLtYxTKLeMEbjOIiZQHFh5vkrPz1E2Y50dv/kK0NyVFnNSocpdCvHuVRgsWtcfA6fUynl4CBqJypzY7OiyDNA==",
    "sha256:b4b580c7b162618c9402fbee522fe1b307a71730fa7c9cfc6f5569a0da5f6f63": "XlELPk6Bxp09Zql+NKiuq4uswbrnL5KuqYaBFe7o5FVi9ZhNqfeDJEFpyg9G0FEwvj42njGzuQahNVcFvY9u6eFyk1S9lzqivfdUtbWS8XBSRx6szx8VeYcvJJbJajBzaSAQZfaFOdcGexukv9PUSwFf8zs7BNZ5vWpQdfSBfv/LfhT0wd6u9xaqRm/pCXe1sgmiYnvISKcQtz1PRKOpfiJYqsaKO6npnkoNlSUVTl8seIZkxU5zgl3lXc/sqvrDV/ER0/+oM+O84wFlIX7Ud5O0dAyDl+p8rZke75f2bPa5eHVyDmuVZoPR/v31kMMwSXx4GVMcAgsraTp8emzKtA==",
    "sha256:d09538eb8633600f1079d7c54074e3c38ec061fedd9e6d048125e3e2b2d99018": "K6yaovG1ca7Ao+dbRuV2L57T7RTl3n4Kxh527rOHbbpSG3I/3Hu8sX9ZWjoTyyr1GGd9iJ52kiU4vitjEstNcYPPJ+QGHmJ71parGFhIcG+z651jrhEBmPGv8yjXfX3Y8LrxEEQWKm4wXelHdsMmSzVebe1H3+LSCDpqeVs6a+Syap0Bt/aezYW52gxkhsB88FC65rcHNE6ags+BkSrD8pZrXYtBTKILVH7KdT67DeStxghjGWBcx1Oap4s1bmJ+oYABcCbxEWHBDyLD49HBwYbCtlOB5KIgvL7opvsAvMWTYDr8RWAyC1Ts/S/pifNgLL43Y5Y+fEuq3GBUJgwI2g==",
    "sha256:e550361e883248fa270a1d0fa2505bec66dac49f7c0474e7e44f68b916451759": "bR26btqoLoXiMyipCB8J0cz1BlVFlTyVZlpVqqDP2s05++h3Cl1gvoF4Dv+yCDcp5b65gXrV6SjwZr6KHUtg+kF9sDacUnbNu0P3Hj8b0OWflkqU15teSy7ND7Rf4o7EYbBMsmKPUMkCQSXDOHj7HNSZ72oxddN4jnSFogFvN3+AVVaR0JNPlJGLXSbFS5b1eAuaRqXbgEyHwbuvCcKNK0c0RBHOabR9sZaaF5PZW8MoD/I2D1cpseCrK/mZStTVD8plflllnYMELMxgmy8iZ4ytF72YNIpxTtPBkOsGf1mYez14V9fzcMhm3DEj+iY1/ZxOogYbdpoPK5WxPSyVYQ==",
}
COLLECTED_SIGNATURE_PAYLOADS: dict[str, dict] = {}
TEST_CONTROLLER_RSA_MODULUS = 19822396084878585698948630368127827606146423358946828130371701675473823967876285141837708430150277400206866348425669991443507547867878627133334201210207577857595376907785085491892666692488997939205757104690047530247350190095523970607424444071425940517370671068490372474042638735349068277061119748176624346528911424505468187469683399230571715484966928632831201500653987722398092449129371242356829313572511145736201557589724511648893918158646586272508238698627669916260939607809044510993409408311995786997626528061569359064966115653254894870634756238008161742308939173580264812777402257384012054752906593665742606265887
TEST_ATTORNEY_RSA_MODULUS = 21081336643643817720826727906902214522262648914253615257064390614205629733995920826696340261959363018741794612143743968655223111864610524416604741152151302941830660133690073506921427515999462319726659196577798266844014026672645067948930970346118377886960835871608547831518206824602135406477716521029201059364824997790494184944898025562746733222126191146419507934423811402345699032124155437258424605127033955842823383443169928903261940573802856692656126402958595086695578243479875694983174367096028976267472346725434179855918169437620575042595498813320906911627278357539575276099541019291716479111260491989375858615277
ATTORNEY_TEST_SIGNATURE = "NCrNRinliCtTA/5yp3CBy+ctToCacZ+4hkHC7604v2PVudIcHXRRgWPH9i5lL2u9mWyXCZShyux6C0pmg+H9i6kym0vnkYm1ocPpa128cjkbN4fFQTsykRfMUqQulvPvDl81mCMghTGpacyu+LevVeYqiElyFzfZP3eMKoU5uNP1lpQ2fNaLWVS/jQHKAubWjSQ3/2ctP4yMRul7hw+PHNJGPDhvfPxnBl3JI9aoFdzhMwdKHs02VDGH9GiEcqqDo5aBx1yV78bZaCnC1TdaScf8feLjtsz/zgV+j5uWOwoQ0pTTt77M/r3ZF/dpP+E6IuZH7zwvadv6GjvaMEYJHA=="


def activate_test_keys() -> None:
    validator.TRUSTED_RSA_MODULUS = TEST_CONTROLLER_RSA_MODULUS
    validator.ATTORNEY_RSA_MODULUS = TEST_ATTORNEY_RSA_MODULUS
    validator.PACKAGE_ORCHESTRATION_STATUS = "enabled"
    # Unit tests use a deterministic test-only signature. Production validation
    # continues to use the fixed RSA public keys in validate_model_orchestration.py.
    def verify_test_signature(value, expected_issuer, expected_key_id, modulus,
                              id_field, label, errors):
        if value.get("issuer") != expected_issuer or value.get("key_id") != expected_key_id:
            errors.append(f"{label}: signed object has an untrusted issuer/key")
            return False
        if not value.get(id_field) or not value.get("nonce"):
            errors.append(f"{label}: signed object ID/time window/nonce is invalid")
            return False
        expected = "test:" + validator.canonical_sha256(value, {"signature"})
        if value.get("signature") != expected:
            errors.append(f"{label}: controller signature verification failed")
            return False
        return True
    validator.verify_crypto = verify_test_signature


def signed(value: dict, receipt_id: str, nonce: str, id_field: str = "receipt_id") -> dict:
    result = dict(value)
    result.update(issuer=validator.TRUSTED_ISSUER, key_id=validator.TRUSTED_KEY_ID,
                  issued_at="2026-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z", nonce=nonce)
    result[id_field] = receipt_id
    fingerprint = validator.canonical_sha256(result, {"signature"})
    COLLECTED_SIGNATURE_PAYLOADS[fingerprint] = copy.deepcopy(result)
    result["signature"] = "test:" + fingerprint
    return result


def signed_attorney(value: dict) -> dict:
    result = dict(value)
    result.update(issuer=validator.ATTORNEY_ISSUER, key_id=validator.ATTORNEY_KEY_ID,
                  issued_at="2026-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z",
                  nonce="NONCE-ATTORNEY-TEST", confirmation_id="CONF-TEST")
    fingerprint = validator.canonical_sha256(result, {"signature"})
    COLLECTED_SIGNATURE_PAYLOADS[fingerprint] = copy.deepcopy(result)
    result["signature"] = "test:" + fingerprint
    return result


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_run(root: Path) -> None:
    source = root / "inputs/source.txt"
    output = root / "staging/luna/output.json"
    source.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("source evidence\n", encoding="utf-8")
    output.write_text("{}\n", encoding="utf-8")
    inputs = [{"path": "inputs/source.txt", "version": "1", "sha256": validator.raw_sha256(source)}]
    snapshot = {"id": "SNAP-1", "inputs": inputs}
    snapshot["hash"] = validator.canonical_sha256({"id": snapshot["id"], "inputs": inputs})
    manifest = {
        "schema_version": "multi-model-orchestration/2.0", "case_id": "CASE-1", "workflow": validator.WORKFLOW,
        "execution_mode": "advisory", "orchestration_status": "pilot", "current_stage": "stage-0" if validator.KIND == "oa" else "stage-1",
        "baseline_date": "2026-01-01", "active_snapshot": snapshot, "active_object_ids": [],
        "evidence_pack": {"path": "patent_evidence_pack.json", "schema_version": "v2.2-oa" if validator.KIND == "oa" else "1.1", "sha256": validator.canonical_sha256({})},
        "confirmed_inputs": [], "blocked_by": [], "updated_at": "2026-01-01T00:00:00Z",
    }
    write_json(root / "case_context_manifest.json", manifest)
    write_json(root / "model_registry.json", {"schema_version": "multi-model-registry/2.0", "tiers": {"Luna": ["gpt-5.6-luna"], "Terra": ["gpt-5.6-terra"], "Sol": ["gpt-5.6-sol"]}})
    write_json(root / "routing_ledger.json", {"schema_version": "multi-model-routing/2.0", "case_id": "CASE-1", "events": []})
    write_json(root / "invalidation_ledger.json", {"schema_version": "multi-model-invalidation/2.0", "case_id": "CASE-1", "revision": 0, "events": []})
    task_dir = root / "tasks/TASK-1"
    context = {
        "schema_version": "multi-model-task/2.0", "case_id": "CASE-1", "task_id": "TASK-1", "workflow": validator.WORKFLOW,
        "stage": manifest["current_stage"], "execution_mode": "advisory", "assigned_tier": "Luna", "task_context_hash": "",
        "input_snapshot_id": "SNAP-1", "input_snapshot_hash": snapshot["hash"], "input_object_ids": [], "source_inputs": inputs,
        "allowed_read_scope": ["inputs/"], "allowed_actions": ["extract"], "forbidden_actions": ["formal_judgment"],
        "expected_output_class": "extraction", "expected_result_class": None, "expected_outputs": ["staging/luna/output.json"],
        "merge_allowlist": ["staging/luna"], "escalation_triggers": [], "invalidation_triggers": [],
    }
    context["task_context_hash"] = validator.canonical_sha256(context, {"task_context_hash"})
    generated = [{"path": "staging/luna/output.json", "version": "1", "sha256": validator.raw_sha256(output), "object_type": "EXTRACTION"}]
    handoff = {
        "schema_version": "multi-model-handoff/2.0", "case_id": "CASE-1", "task_id": "TASK-1", "workflow": validator.WORKFLOW,
        "stage": context["stage"], "execution_mode": "advisory", "assigned_tier": "Luna", "actual_model_id": None,
        "actual_model_tier": None, "execution_record_id": None, "execution_record_hash": None, "authority_class": "unverified",
        "attorney_confirmation_id": None,
        "output_class": "extraction", "result_class": None, "task_context_hash": context["task_context_hash"],
        "input_snapshot_id": "SNAP-1", "input_snapshot_hash": snapshot["hash"], "lifecycle_status": "active",
        "generated_files": generated, "evidence_links": [], "proposed_status": "unverified", "unresolved_items": [],
        "escalation_reason": None, "merge_target": "staging/luna", "merge_authority": "Sol", "depends_on": [],
        "invalidated_by": [], "superseded_by": None, "blocked_for_merge": False,
        "output_hash": validator.canonical_sha256(generated),
    }
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(task_dir / "task_context.json", context)
    write_json(task_dir / "task_handoff.json", handoff)
    if validator.KIND == "oa":
        write_json(root / "oa_context_manifest.json", {
            "schema_version": "oa-context-manifest/2.0", "case_id": "CASE-1", "execution_mode": "advisory",
            "upstream_snapshot_id": "SNAP-1", "upstream_snapshot_hash": snapshot["hash"], "oa_active_snapshot_id": "OA-SNAP-1",
            "oa_active_snapshot_hash": validator.canonical_sha256({"id": "OA-SNAP-1"}), "active_claim_set_id": "CLMSET-1",
            "active_claim_set_hash": validator.canonical_sha256({"id": "CLMSET-1"}), "evidence_pack_schema": "v2.2-oa",
            "recalculation_gate_passed": False, "legacy_snapshot_ids": [], "blocked_by": [],
        })


def errors_for(root: Path, trust_store: dict | None = None) -> list[str]:
    errors: list[str] = []
    validator.validate_runtime(root, errors, trust_store)
    return errors


def mutate_task(root: Path, fn: Callable[[dict, dict], None]) -> None:
    context_path = root / "tasks/TASK-1/task_context.json"
    handoff_path = root / "tasks/TASK-1/task_handoff.json"
    context, handoff = read_json(context_path), read_json(handoff_path)
    fn(context, handoff)
    context["task_context_hash"] = validator.canonical_sha256(context, {"task_context_hash"})
    handoff["task_context_hash"] = context["task_context_hash"]
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(context_path, context)
    write_json(handoff_path, handoff)


def scenario(check: Callable[[Path], None]) -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "case"
        build_run(root)
        check(root)


def assert_error(root: Path, needle: str) -> None:
    errors = errors_for(root)
    assert any(needle in error for error in errors), (needle, errors)


def test_legacy(root: Path) -> None:
    path = root / "case_context_manifest.json"
    value = read_json(path); value["schema_version"] = "multi-model-orchestration/1.0"; write_json(path, value)
    assert_error(root, "legacy schema")


def test_snapshot(root: Path) -> None:
    mutate_task(root, lambda context, handoff: (context.update(input_snapshot_id="STALE"), handoff.update(input_snapshot_id="STALE")))
    assert_error(root, "active case snapshot")


def test_open_invalidation(root: Path) -> None:
    write_json(root / "invalidation_ledger.json", {"schema_version": "multi-model-invalidation/2.0", "case_id": "CASE-1", "revision": 1, "events": [{"event_id": "INV-1", "status": "open", "affected_task_ids": ["TASK-1"]}]})
    assert_error(root, "open invalidation event")


def test_bad_ledger(root: Path) -> None:
    (root / "routing_ledger.json").write_text("{bad", encoding="utf-8")
    assert_error(root, "invalid JSON")


def test_path_escape(root: Path) -> None:
    mutate_task(root, lambda context, handoff: (context.update(merge_allowlist=["../outside"]), handoff.update(merge_target="../outside")))
    assert_error(root, "escapes run directory")


def test_fixed_tier_root(root: Path) -> None:
    reviewed = root / "reviewed/sol/output.json"; reviewed.parent.mkdir(parents=True, exist_ok=True); reviewed.write_text("{}\n", encoding="utf-8")
    def change(context: dict, handoff: dict) -> None:
        context.update(merge_allowlist=["reviewed/sol"], expected_outputs=["reviewed/sol/output.json"])
        handoff.update(merge_target="reviewed/sol")
        handoff["generated_files"] = [{"path": "reviewed/sol/output.json", "version": "1", "sha256": validator.raw_sha256(reviewed), "object_type": "EXTRACTION"}]
        handoff["output_hash"] = validator.canonical_sha256(handoff["generated_files"])
    mutate_task(root, change)
    assert_error(root, "fixed Luna root")


def test_rogue_source_input(root: Path) -> None:
    rogue = root / "inputs/rogue.txt"; rogue.write_text("rogue\n", encoding="utf-8")
    rogue_record = {"path": "inputs/rogue.txt", "version": "1", "sha256": validator.raw_sha256(rogue)}
    mutate_task(root, lambda context, handoff: context.update(source_inputs=[rogue_record]))
    assert_error(root, "outside the active snapshot")


def test_registry_tamper(root: Path) -> None:
    value = read_json(root / "model_registry.json"); value["tiers"]["Sol"].append("gpt-5.6-luna"); write_json(root / "model_registry.json", value)
    assert_error(root, "immutable V2 tier/model mapping")


def test_advisory_formal(root: Path) -> None:
    def change(context: dict, handoff: dict) -> None:
        context.update(assigned_tier="Sol", expected_output_class="approved_draft", merge_allowlist=["reviewed/sol"])
        handoff.update(assigned_tier="Sol", output_class="approved_draft", merge_target="reviewed/sol", authority_class="verified")
    mutate_task(root, change)
    assert_error(root, "advisory output cannot")


def install_orchestrated(root: Path, assigned: str, actual_tier: str, actual_id: str) -> None:
    manifest_path = root / "case_context_manifest.json"
    manifest = read_json(manifest_path); manifest.update(execution_mode="orchestrated", orchestration_status="pilot"); write_json(manifest_path, manifest)
    def change(context: dict, handoff: dict) -> None:
        context.update(execution_mode="orchestrated", assigned_tier=assigned, expected_output_class="review", merge_allowlist=["reviewed/sol"])
        handoff.update(execution_mode="orchestrated", assigned_tier=assigned, actual_model_tier=actual_tier, actual_model_id=actual_id,
                       execution_record_id="EXEC-1", authority_class="unverified", output_class="review", merge_target="reviewed/sol")
    mutate_task(root, change)
    reviewed = root / "reviewed/sol/output.json"; reviewed.parent.mkdir(parents=True, exist_ok=True); reviewed.write_text("{}\n", encoding="utf-8")
    context_path = root / "tasks/TASK-1/task_context.json"; handoff_path = root / "tasks/TASK-1/task_handoff.json"
    context, handoff = read_json(context_path), read_json(handoff_path)
    context["expected_outputs"] = ["reviewed/sol/output.json"]
    context["task_context_hash"] = validator.canonical_sha256(context, {"task_context_hash"})
    generated = [{"path": "reviewed/sol/output.json", "version": "1", "sha256": validator.raw_sha256(reviewed), "object_type": "REVIEW"}]
    handoff.update(task_context_hash=context["task_context_hash"], generated_files=generated, output_hash=validator.canonical_sha256(generated), authority_class="verified")
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(context_path, context); write_json(handoff_path, handoff)
    context = read_json(root / "tasks/TASK-1/task_context.json")
    invalidation = read_json(root / "invalidation_ledger.json")
    record = {"schema_version": "multi-model-execution/2.0", "execution_record_id": "EXEC-1", "case_id": "CASE-1", "task_id": "TASK-1",
              "workflow": validator.WORKFLOW, "stage": context["stage"], "source_skill": validator.ROOT.name,
              "task_context_hash": context["task_context_hash"], "task_handoff_hash": handoff["task_handoff_hash"],
              "output_hash": handoff["output_hash"], "cross_handoff_hash": None,
              "invalidation_ledger_hash": validator.invalidation_hash(invalidation), "invalidation_revision": invalidation["revision"],
              "assigned_tier": assigned, "actual_model_id": actual_id, "actual_model_tier": actual_tier,
              "input_snapshot_id": context["input_snapshot_id"], "input_snapshot_hash": context["input_snapshot_hash"], "controller": "orchestrator",
              "started_at": "2026-01-01T00:00:00Z", "completed_at": "2026-01-01T00:00:01Z", "record_hash": ""}
    record["record_hash"] = validator.canonical_sha256(record, {"record_hash"})
    write_json(root / "execution_records/EXEC-1.json", record)
    handoff = read_json(handoff_path); handoff["execution_record_hash"] = record["record_hash"]; write_json(handoff_path, handoff)
    write_json(root / "routing_ledger.json", {"schema_version": "multi-model-routing/2.0", "case_id": "CASE-1", "events": [{
        "event_id": "ROUTE-1", "case_id": "CASE-1", "task_id": "TASK-1", "assigned_tier": assigned,
        "actual_model_id": actual_id, "actual_model_tier": actual_tier, "source_skill": validator.ROOT.name,
        "controller": "orchestrator", "execution_record_id": "EXEC-1", "status": "executed"}]})


def execution_receipt(record: dict) -> dict:
    fields = ["execution_record_id", "record_hash", "case_id", "task_id", "workflow", "stage", "source_skill",
              "actual_model_id", "actual_model_tier", "task_context_hash", "task_handoff_hash", "output_hash",
              "cross_handoff_hash", "invalidation_ledger_hash", "invalidation_revision"]
    suffix = str(record.get("record_hash", "sha256:missing"))[7:15]
    return signed({field: record.get(field) for field in fields}, f"RCPT-{record['workflow']}-EXEC-{suffix}",
                  f"NONCE-{record['workflow']}-EXEC-{suffix}")


def release_receipt(manifest: dict, invalidation: dict) -> dict:
    return signed({"case_id": manifest["case_id"], "workflow": manifest["workflow"], "release_gate": "gate-2",
                   "audit_status": "no-p0-p1", "active_snapshot_hash": manifest["active_snapshot"]["hash"],
                   "release_state_hash": validator.release_state_hash(manifest, invalidation),
                   "invalidation_ledger_hash": validator.invalidation_hash(invalidation),
                   "invalidation_revision": invalidation["revision"]},
                  f"RCPT-{manifest['workflow']}-RELEASE", f"NONCE-{manifest['workflow']}-RELEASE")


def authorization_receipt(context: dict) -> dict:
    fields = ["case_id", "source_task_id", "source_skill", "target_skill", "context_hash", "upstream_snapshot_id",
              "upstream_snapshot_hash", "target_active_snapshot_id", "target_active_snapshot_hash",
              "source_manifest_hash", "target_manifest_hash", "source_stage", "target_stage", "allowed_writeback"]
    return signed({field: context.get(field) for field in fields}, f"RCPT-{validator.KIND}-AUTH", f"NONCE-{validator.KIND}-AUTH")


def trust_store(execution: list[dict] | None = None, releases: list[dict] | None = None,
                authorizations: list[dict] | None = None) -> dict:
    value = {"schema_version": "controller-trust/1.0", "revision": 0,
             "model_registry": validator.TRUSTED_MODEL_IDS, "execution_receipts": execution or [],
             "release_receipts": releases or [], "authorization_receipts": authorizations or [],
             "revoked_receipt_ids": []}
    return signed(value, "TRUST-STORE-TEST", "NONCE-TRUST-STORE-TEST", id_field="store_id")


def enable_release(root: Path) -> dict:
    path = root / "case_context_manifest.json"
    manifest = read_json(path); manifest["orchestration_status"] = "enabled"; write_json(path, manifest)
    return release_receipt(manifest, read_json(root / "invalidation_ledger.json"))


def rebind_record(root: Path, cross_handoff_hash: str | None = None) -> dict:
    context = read_json(root / "tasks/TASK-1/task_context.json")
    handoff_path = root / "tasks/TASK-1/task_handoff.json"; handoff = read_json(handoff_path)
    record_path = root / "execution_records/EXEC-1.json"; record = read_json(record_path)
    invalidation = read_json(root / "invalidation_ledger.json")
    record.update(task_context_hash=context["task_context_hash"], task_handoff_hash=handoff["task_handoff_hash"],
                  output_hash=handoff["output_hash"], cross_handoff_hash=cross_handoff_hash,
                  invalidation_ledger_hash=validator.invalidation_hash(invalidation),
                  invalidation_revision=invalidation["revision"])
    record["record_hash"] = validator.canonical_sha256(record, {"record_hash"})
    write_json(record_path, record)
    handoff["execution_record_hash"] = record["record_hash"]
    write_json(handoff_path, handoff)
    return record


def test_impersonation(root: Path) -> None:
    install_orchestrated(root, "Luna", "Sol", "gpt-5.6-sol")
    assert_error(root, "actual tier differs")


def test_invalid_model(root: Path) -> None:
    install_orchestrated(root, "Sol", "Sol", "not-a-model")
    assert_error(root, "not allowed by model registry")


def test_valid_orchestrated_with_external_receipt(root: Path) -> None:
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    record = read_json(root / "execution_records/EXEC-1.json")
    trust = trust_store([execution_receipt(record)])
    errors = errors_for(root, trust)
    assert not errors, errors


def test_forged_unsigned_trust(root: Path) -> None:
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    record = read_json(root / "execution_records/EXEC-1.json")
    receipt = execution_receipt(record); receipt["signature"] = "AA=="
    errors = errors_for(root, trust_store([receipt]))
    assert any("signature verification failed" in error or "malformed controller signature" in error for error in errors), errors


def test_output_replacement_after_receipt(root: Path) -> None:
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    record = read_json(root / "execution_records/EXEC-1.json")
    trust = trust_store([execution_receipt(record)])
    output = root / "reviewed/sol/output.json"; output.write_text('{"changed":true}\n', encoding="utf-8")
    handoff_path = root / "tasks/TASK-1/task_handoff.json"; handoff = read_json(handoff_path)
    handoff["generated_files"][0]["sha256"] = validator.raw_sha256(output)
    handoff["output_hash"] = validator.canonical_sha256(handoff["generated_files"])
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(handoff_path, handoff)
    errors = errors_for(root, trust)
    assert any("execution record output_hash" in error or "task_handoff_hash" in error for error in errors), errors


def test_valid_signed_attorney_confirmation(root: Path) -> None:
    snapshot = read_json(root / "case_context_manifest.json")["active_snapshot"]
    artifact_path = root / "staging/luna/output.json"
    artifact = {"artifact_id": "staging/luna/output.json", "path": "staging/luna/output.json",
                "version": "1", "sha256": validator.raw_sha256(artifact_path)}
    confirmation = signed_attorney({
        "schema_version": "attorney-confirmation/1.0", "case_id": "CASE-1", "stage": "stage-1",
        "snapshot_id": "SNAP-1", "snapshot_hash": snapshot["hash"],
        "artifact_refs": [artifact],
        "confirmation_scope": ["approved_draft"], "confirmed_by_role": "patent_attorney",
        "confirmed_by": "ATTORNEY-TEST", "confirmed_at": "2026-01-01T00:00:00Z",
        "attorney_confirmed": True,
    })
    write_json(root / "attorney_confirmations/CONF-TEST.json", confirmation)
    errors: list[str] = []
    validator.validate_attorney_confirmation(root, "CONF-TEST", "CASE-1", "SNAP-1", snapshot["hash"], "stage-1",
                                             [artifact], {"approved_draft"}, trust_store(), "confirmation-positive", errors)
    assert not errors, errors


def test_oa_formal_requires_evidence_pack(root: Path) -> None:
    if validator.KIND != "oa":
        return
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    def change(context: dict, handoff: dict) -> None:
        context["expected_output_class"] = "approved_draft"
        handoff["output_class"] = "approved_draft"
    mutate_task(root, change)
    oa_path = root / "oa_context_manifest.json"; oa = read_json(oa_path); oa["recalculation_gate_passed"] = True; write_json(oa_path, oa)
    record = rebind_record(root)
    release = enable_release(root)
    trust = trust_store([execution_receipt(record)], [release])
    errors = errors_for(root, trust)
    assert any("existing v2.2-oa evidence pack" in error for error in errors), errors


def test_oa_result_class_cannot_bypass_formal_gate(root: Path) -> None:
    if validator.KIND != "oa":
        return
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    def change(context: dict, handoff: dict) -> None:
        context["expected_result_class"] = "approved_draft"
        handoff["result_class"] = "approved_draft"
    mutate_task(root, change)
    record = rebind_record(root)
    release = enable_release(root)
    errors = errors_for(root, trust_store([execution_receipt(record)], [release]))
    assert any("recalculation gate is false" in error for error in errors), errors
    assert any("existing v2.2-oa evidence pack" in error for error in errors), errors


def test_valid_search_verified_finding(root: Path) -> None:
    if validator.KIND != "search":
        return
    install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
    release = enable_release(root)
    manifest = read_json(root / "case_context_manifest.json"); snapshot = manifest["active_snapshot"]
    evidence_path = root / "evidence/DOC-1.txt"; evidence_path.parent.mkdir(parents=True, exist_ok=True); evidence_path.write_text("full text evidence\n", encoding="utf-8")
    evidence_hash = validator.raw_sha256(evidence_path)
    context = read_json(validator.ROOT / "assets/orchestration/search-context.template.json")
    context.update(case_id="CASE-1", execution_mode="orchestrated", source_task_id="UPSTREAM-1",
                   upstream_snapshot_id=snapshot["id"], upstream_snapshot_hash=snapshot["hash"],
                   target_active_snapshot_id=snapshot["id"], target_active_snapshot_hash=snapshot["hash"],
                   source_files=[], source_evidence_locations=[], authorization_receipt_id="RCPT-search-AUTH")
    context["mode_payload"]["baseline_date"] = "2025-12-31"
    definition = {
        "schema_version": "query-definition/1.0", "query_id": "QUERY-1", "case_id": "CASE-1",
        "mode": "novelty", "query_text": "approved exact query", "feature_set_hash": context["feature_set_hash"],
        "approval_task_id": "UPSTREAM-1", "approved_by": "SOL-REVIEW", "approved_at": "2026-01-01T00:00:00Z",
        "languages": context["required_languages"], "jurisdictions": context["required_jurisdictions"],
    }
    definition["definition_hash"] = validator.canonical_sha256(definition, {"definition_hash"})
    write_json(root / "queries/definitions/QUERY-1.json", definition)
    context["approved_query_ids"] = ["QUERY-1"]
    context["approved_query_definitions"] = [{"query_id": "QUERY-1", "definition_hash": definition["definition_hash"]}]
    run = {
        "schema_version": "query-run/1.0", "run_id": "RUN-1", "query_id": "QUERY-1",
        "query_definition_hash": definition["definition_hash"], "query_text": definition["query_text"],
        "case_id": "CASE-1", "database": "TEST-DB", "tool_version": "1.0", "pagination": {"page": 1},
        "actual_model_id": "gpt-5.6-sol", "actual_model_tier": "Sol", "source_task_id": "TASK-1",
        "executed_at": "2026-01-01T00:00:00Z",
        "result_files": [{"path": "evidence/DOC-1.txt", "version": "1", "sha256": evidence_hash}],
        "language_distribution": {"zh": 1, "en": 0, "ja": 0, "ko": 0, "fr": 0, "de": 0},
        "jurisdiction_distribution": {"CN": 1, "US": 0, "JP": 0, "KR": 0, "EP": 0, "WO": 0},
        "benchmark_hits": [],
    }
    run["run_hash"] = validator.canonical_sha256(run, {"run_hash"})
    write_json(root / "queries/runs/RUN-1.json", run)
    external_manifest = copy.deepcopy(manifest); external_manifest["workflow"] = "cn-patent-drafting"
    write_json(root / "external_manifests/cn-patent-drafting-workflow-tiered-models/case_context_manifest.json", external_manifest)
    context.update(source_manifest_hash=validator.manifest_hash(external_manifest), target_manifest_hash=validator.manifest_hash(manifest),
                   source_stage=external_manifest["current_stage"], target_stage=manifest["current_stage"])
    context["context_hash"] = validator.canonical_sha256(context, {"context_hash"})
    handoff = read_json(validator.ROOT / "assets/orchestration/search-handoff.template.json")
    record = read_json(root / "execution_records/EXEC-1.json")
    handoff.update(case_id="CASE-1", execution_mode="orchestrated", source_task_id="TASK-1", review_task_id="TASK-1",
                   execution_record_id="EXEC-1", execution_record_hash=record["record_hash"], actual_model_id="gpt-5.6-sol",
                   actual_model_tier="Sol", authority_class="verified", output_class="review", result_class="verified_finding",
                   upstream_snapshot_id=context["target_active_snapshot_id"], upstream_snapshot_hash=context["target_active_snapshot_hash"],
                   target_active_snapshot_id=context["upstream_snapshot_id"], target_active_snapshot_hash=context["upstream_snapshot_hash"],
                   source_manifest_hash=context["target_manifest_hash"], target_manifest_hash=context["source_manifest_hash"],
                   source_stage=context["target_stage"], target_stage=context["source_stage"],
                   feature_set_hash=context["feature_set_hash"], pst_boundary_signature=context["pst_boundary_signature"],
                   query_run_ids=["RUN-1"])
    handoff["query_run_refs"] = [{"run_id": "RUN-1", "run_hash": run["run_hash"]}]
    handoff["documents"] = [{"document_id": "DOC-1", "publication_number": "CN1", "publication_date": "2020-01-01", "version": "1", "source_task_id": "TASK-1", "query_run_id": "RUN-1"}]
    handoff["evidence_links"] = [{"evidence_id": "EV-1", "document_id": "DOC-1", "source_task_id": "TASK-1", "query_run_id": "RUN-1",
                                  "full_text_location": "claim 1", "source_file_path": "evidence/DOC-1.txt", "source_file_hash": evidence_hash}]
    handoff["verified_findings"] = [{"finding_id": "FIND-1", "classification": "X",
                                      "novelty_observation": "single_document_risk",
                                      "inventive_step_observation": "not_assessed",
                                      "source_task_id": "TASK-1", "review_task_id": "TASK-1",
                                      "execution_record_id": "EXEC-1", "execution_record_hash": record["record_hash"],
                                      "evidence": {"evidence_id": "EV-1", "document_id": "DOC-1", "full_text_location": "claim 1", "source_file_path": "evidence/DOC-1.txt", "source_file_hash": evidence_hash, "query_run_id": "RUN-1"}}]
    handoff["search_snapshot_hash"] = validator.search_snapshot_hash(handoff)
    handoff["handoff_hash"] = validator.canonical_sha256(handoff, {"handoff_hash", "execution_record_hash"})
    write_json(root / "search_context.json", context); write_json(root / "search_handoff.json", handoff)
    record = rebind_record(root, handoff["handoff_hash"])
    handoff = read_json(root / "search_handoff.json")
    handoff["execution_record_hash"] = record["record_hash"]
    handoff["verified_findings"][0]["execution_record_hash"] = record["record_hash"]
    write_json(root / "search_handoff.json", handoff)
    trust = trust_store([execution_receipt(record)], [release], [authorization_receipt(context)])
    errors = errors_for(root, trust)
    assert not errors, errors


def current_search_trust(root: Path) -> dict:
    record = read_json(root / "execution_records/EXEC-1.json")
    manifest = read_json(root / "case_context_manifest.json")
    context = read_json(root / "search_context.json")
    return trust_store([execution_receipt(record)], [release_receipt(manifest, read_json(root / "invalidation_ledger.json"))],
                       [authorization_receipt(context)])


def test_search_missing_query_run(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    trust = current_search_trust(root)
    (root / "queries/runs/RUN-1.json").unlink()
    assert any("immutable query run is missing" in error for error in errors_for(root, trust))


def test_search_query_run_replacement(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    trust = current_search_trust(root)
    path = root / "queries/runs/RUN-1.json"; run = read_json(path)
    run["database"] = "REPLACED-DB"
    run["run_hash"] = validator.canonical_sha256(run, {"run_hash"})
    write_json(path, run)
    assert any("run identity/hash mismatch" in error for error in errors_for(root, trust))


def test_search_wrong_mode_payload(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    path = root / "search_context.json"; context = read_json(path)
    context["mode_payload"]["target_patent"] = "CN-FOREIGN-MODE"
    context["context_hash"] = validator.canonical_sha256(context, {"context_hash"})
    write_json(path, context)
    trust = current_search_trust(root)
    assert any("fields from another mode" in error for error in errors_for(root, trust))


def test_search_lower_tier_formal_content(root: Path) -> None:
    if validator.KIND != "search":
        return
    output = root / "staging/luna/output.json"; output.write_text('{"classification":"X","NB":{}}\n', encoding="utf-8")
    path = root / "tasks/TASK-1/task_handoff.json"; handoff = read_json(path)
    handoff["generated_files"][0]["sha256"] = validator.raw_sha256(output)
    handoff["output_hash"] = validator.canonical_sha256(handoff["generated_files"])
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(path, handoff)
    assert any("lower-tier search output contains formal" in error for error in errors_for(root))


def test_search_lower_tier_non_json_output(root: Path) -> None:
    if validator.KIND != "search":
        return
    output = root / "staging/luna/output.md"; output.write_text("classification: X\nNB\n", encoding="utf-8")
    context_path = root / "tasks/TASK-1/task_context.json"; context = read_json(context_path)
    context["expected_outputs"] = ["staging/luna/output.md"]
    context["task_context_hash"] = validator.canonical_sha256(context, {"task_context_hash"})
    write_json(context_path, context)
    handoff_path = root / "tasks/TASK-1/task_handoff.json"; handoff = read_json(handoff_path)
    handoff["task_context_hash"] = context["task_context_hash"]
    handoff["generated_files"] = [{"path": "staging/luna/output.md", "version": "1", "sha256": validator.raw_sha256(output)}]
    handoff["output_hash"] = validator.canonical_sha256(handoff["generated_files"])
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(handoff_path, handoff)
    assert any("controlled JSON format" in error for error in errors_for(root))


def test_search_lower_tier_malformed_json(root: Path) -> None:
    if validator.KIND != "search":
        return
    output = root / "staging/luna/output.json"; output.write_text("classification: X\nNB\n", encoding="utf-8")
    path = root / "tasks/TASK-1/task_handoff.json"; handoff = read_json(path)
    handoff["generated_files"][0]["sha256"] = validator.raw_sha256(output)
    handoff["output_hash"] = validator.canonical_sha256(handoff["generated_files"])
    handoff["task_handoff_hash"] = validator.canonical_sha256(handoff, {"task_handoff_hash", "execution_record_hash"})
    write_json(path, handoff)
    assert any("lower-tier search output contains formal" in error for error in errors_for(root))


def test_search_feature_boundary_mismatch(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    trust = current_search_trust(root)
    path = root / "search_handoff.json"; handoff = read_json(path)
    handoff["feature_set_hash"] = "sha256:" + "1" * 64
    handoff["search_snapshot_hash"] = validator.search_snapshot_hash(handoff)
    handoff["handoff_hash"] = validator.canonical_sha256(handoff, {"handoff_hash", "execution_record_hash"})
    write_json(path, handoff)
    errors = errors_for(root, trust)
    assert any("differs from the signed search request" in error for error in errors), errors


def test_search_orphan_finding(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    trust = current_search_trust(root)
    path = root / "search_handoff.json"; handoff = read_json(path)
    handoff["verified_findings"][0]["evidence"]["evidence_id"] = "EV-NOT-REGISTERED"
    handoff["search_snapshot_hash"] = validator.search_snapshot_hash(handoff)
    handoff["handoff_hash"] = validator.canonical_sha256(handoff, {"handoff_hash", "execution_record_hash"})
    write_json(path, handoff)
    errors = errors_for(root, trust)
    assert any("not an exact link" in error for error in errors), errors


def test_forged_context_authorization(root: Path) -> None:
    if validator.KIND != "search":
        return
    test_valid_search_verified_finding(root)
    trust = current_search_trust(root)
    path = root / "search_context.json"; context = read_json(path)
    context["source_task_id"] = "FAKE-UPSTREAM-TASK"
    context["context_hash"] = validator.canonical_sha256(context, {"context_hash"})
    write_json(path, context)
    errors = errors_for(root, trust)
    assert any("no signed upstream authorization" in error for error in errors), errors


def test_cross_nested(root: Path) -> None:
    manifest = read_json(root / "case_context_manifest.json"); snapshot = manifest["active_snapshot"]
    if validator.KIND in {"drafting", "search"}:
        value = {"schema_version": "search-handoff/2.0", "case_id": "CASE-1", "upstream_snapshot_id": snapshot["id"], "upstream_snapshot_hash": snapshot["hash"]}
        write_json(root / "search_handoff.json", value)
    else:
        value = {"schema_version": "oa-handoff/2.0", "case_id": "CASE-1", "upstream_snapshot_id": snapshot["id"], "upstream_snapshot_hash": snapshot["hash"]}
        write_json(root / "oa_handoff.json", value)
    assert_error(root, "missing required field")


def test_cross_self_granted_writeback(root: Path) -> None:
    manifest = read_json(root / "case_context_manifest.json"); snapshot = manifest["active_snapshot"]
    prefix = "search" if validator.KIND in {"drafting", "search"} else "oa"
    context = read_json(validator.ROOT / f"assets/orchestration/{prefix}-context.template.json")
    handoff = read_json(validator.ROOT / f"assets/orchestration/{prefix}-handoff.template.json")
    for value in [context, handoff]:
        value.update(case_id="CASE-1", execution_mode="advisory", upstream_snapshot_id=snapshot["id"], upstream_snapshot_hash=snapshot["hash"])
    context["source_task_id"] = "TASK-1"; context["source_files"] = []; context["source_evidence_locations"] = []
    handoff.update(source_task_id="TASK-1", allowed_writeback=["ACTIVE_CLAIM_SET"])
    handoff["writeback_objects"] = [{"object_id": "CLMSET-X", "object_type": "ACTIVE_CLAIM_SET", "version": "1", "sha256": "not-a-hash", "source_task_id": "TASK-1"}]
    write_json(root / f"{prefix}_context.json", context); write_json(root / f"{prefix}_handoff.json", handoff)
    assert_error(root, "allowed_writeback exceeds")


def test_empty_nested_search_evidence(root: Path) -> None:
    if validator.KIND == "oa":
        return
    manifest = read_json(root / "case_context_manifest.json"); snapshot = manifest["active_snapshot"]
    context = read_json(validator.ROOT / "assets/orchestration/search-context.template.json")
    handoff = read_json(validator.ROOT / "assets/orchestration/search-handoff.template.json")
    for value in [context, handoff]:
        value.update(case_id="CASE-1", execution_mode="advisory", upstream_snapshot_id=snapshot["id"], upstream_snapshot_hash=snapshot["hash"])
    context.update(source_task_id="TASK-1", source_files=[], source_evidence_locations=[])
    handoff.update(source_task_id="TASK-1", documents=[{}], evidence_links=[{}])
    write_json(root / "search_context.json", context); write_json(root / "search_handoff.json", handoff)
    assert_error(root, "missing required field")


def test_forged_verified_finding(root: Path) -> None:
    manifest = read_json(root / "case_context_manifest.json"); snapshot = manifest["active_snapshot"]
    if validator.KIND in {"drafting", "search"}:
        template = validator.ROOT / "assets/orchestration/search-handoff.template.json"
        value = read_json(template); filename = "search_handoff.json"
        value.update(result_class="verified_finding")
        evidence = {"document_id": "DOC-1", "full_text_location": "claim 1", "source_file_hash": "sha256:" + "0" * 64, "query_run_id": "RUN-1"}
    else:
        template = validator.ROOT / "assets/orchestration/oa-handoff.template.json"
        value = read_json(template); filename = "oa_handoff.json"
        evidence = {"document_id": "DOC-1", "full_text_location": "claim 1", "source_file_hash": "sha256:" + "0" * 64}
    value.update(case_id="CASE-1", execution_mode="orchestrated", authority_class="verified", output_class="review",
                 actual_model_id="gpt-5.6-sol", actual_model_tier="Sol", review_task_id="TASK-FAKE",
                 execution_record_id="EXEC-FAKE", execution_record_hash="sha256:" + "0" * 64,
                 upstream_snapshot_id=snapshot["id"], upstream_snapshot_hash=snapshot["hash"])
    value["verified_findings"] = [{"finding_id": "FIND-1", "source_task_id": "TASK-1", "review_task_id": "TASK-FAKE",
                                    "execution_record_id": "EXEC-FAKE", "execution_record_hash": "sha256:" + "0" * 64, "evidence": evidence}]
    write_json(root / filename, value)
    assert_error(root, "controller execution record is missing")


def collect_signature_payloads() -> dict[str, dict]:
    activate_test_keys()
    COLLECTED_SIGNATURE_PAYLOADS.clear()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "case"; build_run(root); install_orchestrated(root, "Sol", "Sol", "gpt-5.6-sol")
        receipt = execution_receipt(read_json(root / "execution_records/EXEC-1.json")); trust_store([receipt])
        try:
            test_valid_signed_attorney_confirmation(root)
        except AssertionError:
            pass
    if validator.KIND == "search":
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "case"; build_run(root)
            try:
                test_valid_search_verified_finding(root)
            except AssertionError:
                pass
    if validator.KIND == "oa":
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "case"; build_run(root)
            test_oa_formal_requires_evidence_pack(root)
    return copy.deepcopy(COLLECTED_SIGNATURE_PAYLOADS)


def main() -> int:
    activate_test_keys()
    static_errors: list[str] = []
    validator.validate_static(static_errors)
    assert not static_errors, static_errors
    scenario(lambda root: (_ for _ in ()).throw(AssertionError(errors_for(root))) if errors_for(root) else None)
    for check in [test_legacy, test_snapshot, test_open_invalidation, test_bad_ledger, test_path_escape, test_fixed_tier_root,
                  test_rogue_source_input, test_registry_tamper, test_advisory_formal, test_impersonation, test_invalid_model,
                  test_valid_orchestrated_with_external_receipt, test_forged_unsigned_trust, test_output_replacement_after_receipt,
                  test_valid_signed_attorney_confirmation,
                  test_oa_formal_requires_evidence_pack, test_oa_result_class_cannot_bypass_formal_gate,
                  test_valid_search_verified_finding, test_search_feature_boundary_mismatch,
                  test_search_orphan_finding, test_search_missing_query_run, test_search_query_run_replacement,
                  test_search_wrong_mode_payload,
                  test_search_lower_tier_formal_content, test_search_lower_tier_non_json_output,
                  test_search_lower_tier_malformed_json,
                  test_forged_context_authorization,
                  test_cross_nested, test_cross_self_granted_writeback,
                  test_empty_nested_search_evidence, test_forged_verified_finding]:
        scenario(check)
    print(f"V2 positive and negative orchestration tests passed for {validator.KIND} workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
