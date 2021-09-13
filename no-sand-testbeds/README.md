# No-SAND testbeds

This folder contains different testbeds, which do not use OpenSAND for the satellite simulation. They rather connect directly instead over a simulated satellite link. This allows for more general debugging and bugfixing of QPEP.

Note: For the alpine and ubuntu testbed the 'alpine-base' and 'ubuntu-base' from the ../docker folder must be built beforehand. QPEP has to be inserted as a binary for the respective architecture, as seen in the ./terminal or ./ws-sat folder.