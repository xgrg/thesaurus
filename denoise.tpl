warning off;
beta=1;
rician=1;  % 1 for rician noise model and 0 for gaussian noise model.
nbthreads=32; % number of threads submit
verbose=0;
cname = '$source';
V=spm_vol('$source');
ima=spm_read_vols(V);

s=size(ima);
ima = double(ima);

%Add path
addpath '/home/grg/denoising/DWIDenoisingPackage_r01_pcode/spm8';
addpath '/home/grg/denoising/DWIDenoisingPackage_r01_pcode/gui';
packagepath = '/home/grg/denoising/DWIDenoisingPackage_r01_pcode';
addpath(genpath(fullfile(packagepath, 'DWIDenoisingPackage')));

dirname = sprintf('%s.bvec',cname(1:end-4));

if(exist(dirname))
    dir = load(dirname);
    if (size(dir,2)~=3)
	dir = dir';
    end
    if (size(dir,2)~=3)
	disp('your format for gradient direction is not correct')
	return
    end
else

    dir = directiondetection(ima);
    if (size(dir,2)~=3)
	dir = dir';
    end
    if (size(dir,2)~=3)
	disp('your format for gradient direction is not correct')
	return
    end
end

% fixed range
map = isnan(ima(:));
ima(map) = 0;
map = isinf(ima(:));
ima(map) = 0;
mini = min(ima(:));
ima = ima - mini;
maxi=max(ima(:));
ima=ima*255/maxi;

[fima] = DWIDenoisingLPCA(ima, beta, rician, nbthreads, verbose);

% save result
ss=size(V);
for ii=1:ss(1)
    V(ii).fname='$target';
    spm_write_vol(V(ii), fima(:,:,:,ii));
end

