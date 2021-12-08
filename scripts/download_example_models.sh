mkdir -p models/
cd models/

# # German
# wget http://ltdata1.informatik.uni-hamburg.de/kaldi_tuda_de/de_683k_nnet3chain_tdnn1f_2048_sp_bi_smaller_fst.tar.bz2
# tar xvfj de_683k_nnet3chain_tdnn1f_2048_sp_bi_smaller_fst.tar.bz2

# English
MODEL_FILE=en_160k_nnet3chain_tdnn1f_2048_sp_bi.tar.bz2
if [ ! -f $MODEL_FILE ]; then
    wget http://ltdata1.informatik.uni-hamburg.de/pykaldi/$MODEL_FILE
    tar xvfj en_160k_nnet3chain_tdnn1f_2048_sp_bi.tar.bz2
    rm en_160k_nnet3chain_tdnn1f_2048_sp_bi.tar.bz2
fi

cd -
