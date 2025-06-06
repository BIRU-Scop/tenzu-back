# Copyright (C) 2024 BIRU
#
# This file is part of Tenzu.
#
# Tenzu is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# You can contact BIRU at ask@biru.sh

# Copyright 2021 Ezeudoh Tochukwu
# https://github.com/eadwinCode/django-ninja-jwt
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


PRIVATE_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA3xMJfyl8TOdrsjDLSIodsArJ/NnQB3ZdfbFC5onxATDfRLLA
CHFo3ye694doBKeSe1NFYbfXPvahl6ODX1a23oQyoRQwlL+M99cLcdCa0gGuJXdb
AaF6Em8E+7uSb3290mI+rZmjqyc7gMtKVWKL4e5i2PerFFBoYkZ7E90KOp2t0ZAD
x2uqF4VTOfYLHG0cPgSw9/ptDStJqJVAOiRRqbv0j0GOFMDYNcN0mDlnpryhQFbQ
iMqn4IJIURZUVBJujFSa45cJPvSmMb6NrzZ1crg5UN6/5Mu2mxQzAi21+vpgGL+E
EuekUd7sRgEAjTHjLKzotLAGo7EGa8sL1vMSFwIDAQABAoIBAQCGGWabF/BONswq
CWUazVR9cG7uXm3NHp2jIr1p40CLC7scDCyeprZ5d+PQS4j/S1Ema++Ih8CQbCjG
BJjD5lf2OhhJdt6hfOkcUBzkJZf8aOAsS6zctRqyHCUtwxuLhFZpM4AkUfjuuZ3u
lcawv5YBkpG/hltE0fV+Jop0bWtpwiKxVsHXVcS0WEPXic0lsOTBCw8m81JXqjir
PCBOnkxgNpHSt69S1xnW3l9fPUWVlduO3EIZ5PZG2BxU081eZW31yIlKsDJhfgm6
R5Vlr5DynqeojAd6SNliCzNXZP28GOpQBrYIeVQWA1yMANvkvd4apz9GmDrjF/Fd
g8Chah+5AoGBAPc/+zyuDZKVHK7MxwLPlchCm5Zb4eou4ycbwEB+P3gDS7MODGu4
qvx7cstTZMuMavNRcJsfoiMMrke9JrqGe4rFGiKRFLVBY2Xwr+95pKNC11EWI1lF
5qDAmreDsj2alVJT5yZ9hsAWTsk2i+xj+/XHWYVkr67pRvOPRAmGMB+NAoGBAOb4
CBHe184Hn6Ie+gSD4OjewyUVmr3JDJ41s8cjb1kBvDJ/wv9Rvo9yz2imMr2F0YGc
ytHraM77v8KOJuJWpvGjEg8I0a/rSttxWQ+J0oYJSIPn+eDpAijNWfOp1aKRNALT
pboCXcnSn+djJFKkNJ2hR7R/vrrM6Jyly1jcVS0zAoGAQpdt4Cr0pt0YS5AFraEh
Mz2VUArRLtSQA3F69yPJjlY85i3LdJvZGYVaJp8AT74y8/OkQ3NipNP+gH3WV3hu
/7IUVukCTcsdrVAE4pe9mucevM0cmie0dOlLAlArCmJ/Axxr7jbyuvuHHrRdPT60
lr6pQr8afh6AKIsWhQYqIeUCgYA+v9IJcN52hhGzjPDl+yJGggbIc3cn6pA4B2UB
TDo7F0KXAajrjrzT4iBBUS3l2Y5SxVNA9tDxsumlJNOhmGMgsOn+FapKPgWHWuMU
WqBMdAc0dvinRwakKS4wCcsVsJdN0UxsHap3Y3a3+XJr1VrKHIALpM0fmP31WQHG
8Y1eiwKBgF6AYXxo0FzZacAommZrAYoxFZT1u4/rE/uvJ2K9HYRxLOVKZe+89ki3
D7AOmrxe/CAc/D+nNrtUIv3RFGfadfSBWzyLw36ekW76xPdJgqJsSz5XJ/FgzDW+
WNC5oOtiPOMCymP75oKOjuZJZ2SPLRmiuO/qvI5uAzBHxRC1BKdt
-----END RSA PRIVATE KEY-----
"""

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3xMJfyl8TOdrsjDLSIod
sArJ/NnQB3ZdfbFC5onxATDfRLLACHFo3ye694doBKeSe1NFYbfXPvahl6ODX1a2
3oQyoRQwlL+M99cLcdCa0gGuJXdbAaF6Em8E+7uSb3290mI+rZmjqyc7gMtKVWKL
4e5i2PerFFBoYkZ7E90KOp2t0ZADx2uqF4VTOfYLHG0cPgSw9/ptDStJqJVAOiRR
qbv0j0GOFMDYNcN0mDlnpryhQFbQiMqn4IJIURZUVBJujFSa45cJPvSmMb6NrzZ1
crg5UN6/5Mu2mxQzAi21+vpgGL+EEuekUd7sRgEAjTHjLKzotLAGo7EGa8sL1vMS
FwIDAQAB
-----END PUBLIC KEY-----
"""

PRIVATE_KEY_2 = """
-----BEGIN RSA PRIVATE KEY-----
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
-----END RSA PRIVATE KEY-----
"""

PUBLIC_KEY_2 = """
-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAwpwcivLRv5T/2pb9zZpf
h4Fy1vla3vm5N2WtkhjB0DX1HmOhSN9O1Q3byW9VLQtuNAdZ8+hc2jU5DIVApFF+
b1Uo1C76qZWOLLwK/yvweACTdT4MISeYHaUd/B7YUNtUQEZF0xxjMM8jRXEuI902
pLEUBx9cd2d8KzCgXyC2dsNIt3zgWCu6RhL1V10lhBXMwl0N1+DAIRsXjCazwaxB
MrTNOsXrex98aaPk3++V1KkPbLnVZk8I7dbpt9EYSvMB7DaXFiLL4XySamFfYmtq
9n9bxKXxnzpObolWkD0SbioaxkCqvEFyy2/y4ZIxYC1mHhRgTtSicnk8WGOgv6Ax
1sRHpbRVDtXMmDHn7oiJdd8YCGvT9AQoibeccPUZbwaiuiULSVjphKErXLg7nH6/
ct8bVYZnh0GnYTljC3O0f3/D1A9ZPxLHJPc9K2GCmZ+TNMmDDmGbLz/TgFiSZE3C
QEORxbGyNh5MZuIrGub9xaKB4HonRf8HXwVa/zL4dKxpzYzHNBH8wqPOWCLXjp65
lcMW7JBAnrqshI0wOCEbk13uLudBaNL4k/h9M9RKaEW24tKpg29XsWu9II3Bt94x
7gwhokE7gICsycUSQWTGaBovbvn0C8k4gkPq6teGAD6AJ6/YV2hiPbdoRL5EkMS3
E01hmaHk9xlOpo73IjUxhXUCAwEAAQ==
-----END PUBLIC KEY-----
"""


ES256_PRIVATE_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIMtBPxiLHcJCrAGdz4jHvTtAh6Rw7351AckG3whXq2WOoAoGCCqGSM49
AwEHoUQDQgAEMZHyNxbkr7+zqQ1dQk/zug2pwYdztmjhpC+XqK88q5NfIS1cBYYt
zhHUS4vGpazNqbW8HA3ZIvJRmx4L96O6/w==
-----END EC PRIVATE KEY-----
"""

ES256_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEMZHyNxbkr7+zqQ1dQk/zug2pwYdz
tmjhpC+XqK88q5NfIS1cBYYtzhHUS4vGpazNqbW8HA3ZIvJRmx4L96O6/w==
-----END PUBLIC KEY-----
"""
