python3 make_combine_workspace.py &> log;
cd cards;
# combineTool.py -M T2W -i ee/* -o workspace.root --parallel 4 &> ../combineLog
# combineTool.py -M Asymptotic -d */*/workspace.root --there -n .limit --parallel 4 &> ../asymptoticLog
# combineTool.py -M AsymptoticGrid ../grid_scan.json -d */*/workspace.root --there &> ../asymptoticLog
# launch FitDiagnostics on a specific point (ee/2.7)
cd ee/2.1;
text2workspace.py Xee_ee_0_2023.txt;
combine -M FitDiagnostics Xee_ee_0_2023.root \
        --saveShapes -n .fitDiagnostics \
        --setParameterRanges mass=2,4.2 \
        --skipSBFit \
        --setRobustFitTolerance 0.3 \
        --setRobustFitStrategy 0 \
        --nllbackend combine \
        --redefineSignalPOIs r \
        -v -1 &> fitDiagnostics.log;

combine -M FitDiagnostics Xee_ee_0_2023.root --setParameterRanges mass=2,4.2 --setRobustFitTolerance 0.3 -v -1
        --saveShapes -n .fitDiagnostics \
        --skipSBFit \
        --setRobustFitStrategy 0 \
        --nllbackend combine \
        --redefineSignalPOIs r \
        -v -1 &> fitDiagnostics.log;

combine -M FitDiagnostics Xee_ee_0_2023.root \
        --skipSBFit \
        --saveShapes \
        --robustFit 1 \
        --setParameterRanges mass=2,4.2 \
        --setRobustFitStrategy 0 \
        --setRobustFitTolerance 10 \
        --cminDefaultMinimizerType Minuit \
        --cminDefaultMinimizerAlgo Migrad \
        --maxFailedSteps 100 \
        --keepFailures \
        -v 1 &> fitDiagnostics.log;
        # --setParameters a0=3.71,a1=-0.9,a2=1.62,a3=3.4,a4=-4.4 \
        # --freezeParameters a0,a1,a2,a3,a4 \
        # --freezeParameters mass,a0,a1,a2,a3,a4,sigma_jpsi,sigma_psi2s,mean_jpsi,mean_psi2s,alphaL_jpsi,alphaL_psi2s,alphaR_jpsi,alphaR_psi2s,nL_jpsi,nL_psi2s \


allConstrainedNuisances

combine -M FitDiagnostics Xee_ee_0_2023.root --saveShapes -n .fitDiagnostics --setParameterRanges mass=2,4.2 --skipSBFit --setRobustFitStrategy 0 --nllbackend combine -v -1


# 
# --plots
# --redefineSignalPOIs r 
# --cminDefaultMinimizerStrategy 0 